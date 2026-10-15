<#
.SYNOPSIS
  Apply selected fixes. Run ELEVATED (Administrator).
  Creates a System Restore point first, then applies only the fix IDs passed in.

.PARAMETER FixIds
  Comma-separated list of fix_id values from scan_health.ps1.

.PARAMETER WhatIf
  Dry-run: show what would be done, change nothing.

.EXAMPLE
  .\apply_changes.ps1 -FixIds "net_dns_optimize,sec_smb1_disable"
#>

param(
  [Parameter(Mandatory=$true)]
  [string[]]$FixIds,
  [switch]$WhatIf
)

$ErrorActionPreference = 'Continue'
$results = @()

function Add-Result {
  param([string]$id, [bool]$success, [string]$message)
  $script:results += [PSCustomObject]@{
    fix_id  = $id
    success = $success
    message = $message
  }
}

# --- Admin check ---
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Error "必须以管理员身份运行。右键 PowerShell -> 以管理员身份运行。"
  exit 1
}

# --- Restore point ---
if (-not $WhatIf) {
  try {
    Enable-ComputerRestore -Drive "$env:SystemDrive\" -ErrorAction SilentlyContinue
    Checkpoint-Computer -Description "WinSecOpt before: $(($FixIds -join ','))" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
    Add-Result 'restore_point' $true "已创建系统还原点"
  } catch {
    Add-Result 'restore_point' $false "创建还原点失败: $_。请手动确认后继续。"
    Write-Warning "还原点创建失败，但继续执行。"
  }
} else {
  Add-Result 'restore_point' $true "[WhatIf] 将创建系统还原点"
}

# --- Fix functions ---

function Invoke-Fix {
  param([string]$Id, [scriptblock]$Action)
  if ($WhatIf) {
    Add-Result $Id $true "[WhatIf] 将执行: $Id"
    return
  }
  try {
    & $Action
    Add-Result $Id $true "已应用"
  } catch {
    Add-Result $Id $false "失败: $_"
  }
}

foreach ($fix in $FixIds) {
  switch -Wildcard ($fix) {

    # ===== NETWORK =====
    'net_dns_optimize' {
      Invoke-Fix $fix {
        # Set DNS on all active physical adapters to Ali + Tencent
        $adapters = Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' }
        foreach ($a in $adapters) {
          Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses ('223.5.5.5','119.29.29.29')
        }
        Clear-DnsClientCache
      }
    }

    'net_nic_power_disable' {
      Invoke-Fix $fix {
        $nics = Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' }
        foreach ($nic in $nics) {
          Set-NetAdapterPowerManagement -Name $nic.Name -AllowComputerToTurnOffDevice Disabled
        }
      }
    }

    'net_tcp_autotune_reset' {
      Invoke-Fix $fix {
        netsh interface tcp set global autotuninglevel=normal | Out-Null
      }
    }

    # ===== SECURITY =====
    'sec_smb1_disable' {
      Invoke-Fix $fix {
        Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue | Out-Null
        Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force | Out-Null
      }
    }

    'sec_uac_max' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name ConsentPromptBehaviorAdmin -Value 2 -Type DWord
      }
    }

    'sec_uac_enable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name EnableLUA -Value 1 -Type DWord
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name ConsentPromptBehaviorAdmin -Value 2 -Type DWord
      }
    }

    'sec_defender_enable' {
      Invoke-Fix $fix {
        Set-MpPreference -DisableRealtimeMonitoring $false
      }
    }

    'sec_fw_enable_domain' {
      Invoke-Fix $fix { Set-NetFirewallProfile -Name Domain -Enabled True }
    }
    'sec_fw_enable_private' {
      Invoke-Fix $fix { Set-NetFirewallProfile -Name Private -Enabled True }
    }
    'sec_fw_enable_public' {
      Invoke-Fix $fix { Set-NetFirewallProfile -Name Public -Enabled True }
    }

    'sec_rdp_disable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 1 -Type DWord
      }
    }

    'sec_guest_disable' {
      Invoke-Fix $fix {
        Disable-LocalUser -Name 'Guest'
      }
    }

    'sec_ports_block' {
      Invoke-Fix $fix {
        # Block inbound SMB/RPC/RDP from public profile
        $ports = @(135,139,445,3389)
        foreach ($p in $ports) {
          Get-NetFirewallRule -DisplayName "Block_Inbound_Port_$p" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
          New-NetFirewallRule -DisplayName "Block_Inbound_Port_$p" -Direction Inbound -Action Block -Protocol TCP -LocalPort $p -Profile Public | Out-Null
        }
      }
    }

    # ===== STABILITY =====
    'stab_startup_review' {
      Add-Result $fix $false "需要手动在任务管理器 -> 启动 tab 禁用，脚本不自动禁用（避免误关必要程序）"
    }

    'stab_pagefile_auto' {
      Invoke-Fix $fix {
        $cs = Get-WmiObject Win32_ComputerSystem
        if (-not $cs.AutomaticManagedPagefile) {
          $cs.AutomaticManagedPagefile = $true
          $cs.Put() | Out-Null
        }
      }
    }

    'stab_autoreboot_off' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl' -Name AutoReboot -Value 0 -Type DWord
      }
    }

    'stab_dump_set' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl' -Name CrashDumpEnabled -Value 7 -Type DWord
      }
    }

    'stab_8dot3_disable' {
      Invoke-Fix $fix {
        fsutil behavior set disable8dot3 1 | Out-Null
      }
    }

    # ===== PRIVACY =====
    'priv_telemetry_min' {
      Invoke-Fix $fix {
        New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Force | Out-Null
        Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Name AllowTelemetry -Value 1 -Type DWord
      }
    }

    'priv_adid_off' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo' -Name Enabled -Value 0 -Type DWord
      }
    }

    'priv_bgapps_off' {
      Invoke-Fix $fix {
        New-Item -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications' -Force | Out-Null
        Set-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications' -Name GlobalDisabled -Value 1 -Type DWord
      }
    }

    'priv_activity_off' {
      Invoke-Fix $fix {
        New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System' -Force | Out-Null
        Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System' -Name EnableActivityFeed -Value 0 -Type DWord
      }
    }

    'priv_tailored_off' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy' -Name TailoredExperiencesWithDiagnosticDataEnabled -Value 0 -Type DWord
      }
    }

    'priv_location_deny' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location' -Name Value -Value 'Deny'
      }
    }

    # ===== GAMING / POWER =====
    'perf_gamedvr_off' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKCU:\System\GameConfigStore' -Name GameDVR_Enabled -Value 0 -Type DWord
        Set-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR' -Name AppCaptureEnabled -Value 0 -Type DWord
      }
    }

    'perf_powerplan_high' {
      Invoke-Fix $fix {
        # Try to set High performance (GUID 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c | Out-Null
      }
    }

    'sec_lock_set' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name ScreenSaveActive -Value '1'
        Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name ScreenSaveTimeOut -Value '1800'
        Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name ScreenSaverIsSecure -Value '1'
      }
    }

    'stab_hiberfil_off' {
      Invoke-Fix $fix {
        powercfg /h off | Out-Null
      }
    }

    # ===== DEEP SECURITY FIXES (white-hat) =====
    'sec_lsa_ppl_enable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RunAsPPL -Value 1 -Type DWord
      }
    }

    'sec_wdigest_disable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\Wdigest' -Name UseLogonCredential -Value 0 -Type DWord
      }
    }

    'sec_pagefile_clear_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' -Name ClearPageFileAtShutdown -Value 1 -Type DWord
      }
    }

    'sec_limit_blank_enable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LimitBlankPasswordUse -Value 1 -Type DWord
      }
    }

    'sec_aie_disable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated -Value 0 -Type DWord -ErrorAction SilentlyContinue
        Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated -Value 0 -Type DWord -ErrorAction SilentlyContinue
      }
    }

    'sec_auto_logon_disable' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name AutoAdminLogon -Value '0'
        Remove-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name DefaultPassword -ErrorAction SilentlyContinue
      }
    }

    'sec_smb_signing_require' {
      Invoke-Fix $fix {
        Set-SmbServerConfiguration -RequireSecuritySignature $true -Force | Out-Null
      }
    }

    'sec_ntlm_level_set' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LmCompatibilityLevel -Value 3 -Type DWord
      }
    }

    'sec_restrict_anon_set' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RestrictAnonymous -Value 1 -Type DWord
      }
    }

    'sec_appinit_clear' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows' -Name AppInit_DLLs -Value ''
        Set-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Windows' -Name AppInit_DLLs -Value ''
      }
    }

    'sec_asr_enable' {
      Invoke-Fix $fix {
        # Microsoft recommended ASR rules GUIDs (Block = 1)
        $rules = @(
          'be1bad49-22f6-4876-82cd-0b66a107d8f9',  # Block abuse of exploited vulnerable signed drivers
          'd3e037e1-3eb8-44c8-a917-57927947560d',  # Block untrusted/unsigned process in %programfiles%
          '56a863a9-875e-4185-98a7-b882c64b5ce5',  # Block from USB
          '92e97fa1-2edf-4476-bdd6-9dd0ddb4dc00',  # Block JS/VBS downloading exe
          'd4f940ab-401b-4efc-aadc-ad5f3c50688a',  # Block Office apps creating child
          'beb3d3b8-e961-4a12-ac0d-f90711af21a2',  # Block Office injecting into other proc
          '01443614-cd74-433a-b99e-2ecdc07bfc25',  # Block Office from running executable
          'e6db77e5-3df2-4cf1-b95a-636979351e5b',  # Block Office communication app creating child
          'c1db55ab-c2dc-4465-a364-987651807b37'   # Block persistence via WMI event
        )
        Set-MpPreference -AttackSurfaceReductionRules_Ids $rules -AttackSurfaceReductionRules_Actions (1..$rules.Count | ForEach-Object { 1 })
      }
    }

    'sec_cfa_enable' {
      Invoke-Fix $fix {
        Set-MpPreference -EnableControlledFolderAccess Enabled
      }
    }

    # ===== FORTRESS LEVEL =====
    'sec_hosts_reset' {
      Invoke-Fix $fix {
        # Backup then reset hosts to default (only localhost entries)
        $hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
        Copy-Item $hosts "$hosts.bak_$(Get-Date -f yyyyMMddHHmmss)" -Force
        Set-Content $hosts @"
# Copyright (c) 1993-2009 Microsoft Corp.
127.0.0.1       localhost
::1             localhost
"@ -Encoding ASCII
      }
    }

    'sec_hvci_enable' {
      Invoke-Fix $fix {
        New-Item -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -Force | Out-Null
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -Name Enabled -Value 1 -Type DWord
      }
    }

    'sec_smartscreen_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer' -Name SmartScreenEnabled -Value 'RequireAdmin'
      }
    }

    'dev_ps_remotesigned' {
      Invoke-Fix $fix {
        Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
      }
    }

    # ===== v6 NETWORK HARDENING =====
    'sec_rdp_harden' {
      Invoke-Fix $fix {
        # Enable NLA + TLS security layer on RDP
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1 -Type DWord
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name SecurityLayer -Value 2 -Type DWord
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name MinEncryptionLevel -Value 3 -Type DWord
      }
    }

    'sec_netbios_off' {
      Invoke-Fix $fix {
        Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces' | ForEach-Object {
          Set-ItemProperty $_.PSPath -Name NetbiosOptions -Value 2 -Type DWord
        }
      }
    }

    'sec_smb_client_sign_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' -Name RequireSecuritySignature -Value 1 -Type DWord
      }
    }

    'sec_netlogon_sign_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters' -Name SignSecureChannel -Value 1 -Type DWord
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters' -Name SealSecureChannel -Value 1 -Type DWord
      }
    }

    # ===== v5 ACADEMIC FIXES =====
    'sec_pwd_hardening' {
      Invoke-Fix $fix {
        $tmpInf = "$env:TEMP\sec_pwd.inf"
        $tmpDb  = "$env:TEMP\sec_pwd.sdb"
        @"
[Version]
signature="`$CHICAGO`$"
[System Access]
MinimumPasswordLength = 14
PasswordComplexity = 1
MaximumPasswordAge = 60
MinimumPasswordAge = 1
PasswordHistorySize = 5
LockoutBadCount = 5
ResetLockoutCount = 30
LockoutDuration = 30
"@ | Out-File $tmpInf -Encoding ASCII
        secedit /configure /db $tmpDb /cfg $tmpInf /areas SECURITYPOLICY | Out-Null
        Remove-Item $tmpInf, $tmpDb -ErrorAction SilentlyContinue
      }
    }

    'audit_ps_logging_on' {
      Invoke-Fix $fix {
        New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' -Force | Out-Null
        Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' -Name EnableScriptBlockLogging -Value 1 -Type DWord
      }
    }

    'sec_llmnr_off' {
      Invoke-Fix $fix {
        New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient' -Force | Out-Null
        Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient' -Name EnableMulticast -Value 0 -Type DWord
      }
    }

    'sec_anon_sam_block' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RestrictAnonymousSAM -Value 1 -Type DWord
      }
    }

    'sec_no_lmhash_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name NoLMHash -Value 1 -Type DWord
      }
    }

    'sec_no_lastuser_on' {
      Invoke-Fix $fix {
        Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name DontDisplayLastUserName -Value 1 -Type DWord
      }
    }

    'sec_psv2_disable' {
      Invoke-Fix $fix {
        Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2 -NoRestart | Out-Null
      }
    }

    default {
      Add-Result $fix $false "未知的 fix_id: $fix"
    }
  }
}

# Output
[PSCustomObject]@{
  applied_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  what_if    = $WhatIf.IsPresent
  results    = $results
} | ConvertTo-Json -Depth 5
