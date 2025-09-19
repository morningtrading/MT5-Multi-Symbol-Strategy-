#Requires -Version 5.1
<#
.SYNOPSIS
    Script automatisé pour ajouter un nouveau symbole au système NewStratSIMPLE
    
.DESCRIPTION
    Ce script automatise complètement l'ajout d'un nouveau symbole de trading :
    1. Ajoute le symbole à la liste principale
    2. Lance le screening des symboles
    3. Met à jour la configuration de risque
    4. Lance les tests complets
    5. Vérifie l'intégration
    
.PARAMETER Symbol
    Le nom exact du symbole à ajouter (ex: XAGUSD, EURUSD, BTCUSD)
    
.PARAMETER AssetClass
    La classe d'actif du symbole :
    - forex : Paires de devises (EURUSD, GBPUSD, etc.)
    - crypto : Cryptomonnaies (BTCUSD, ETHUSD, etc.)
    - index : Indices boursiers (NAS100, SP500ft, etc.)
    - commodity : Matières premières (USOUSD, etc.)
    - precious_metal : Métaux précieux (XAUUSD, XAGUSD, etc.)
    
.PARAMETER Coefficient
    Coefficient de taille de position (défaut: 1, conservateur)
    
.PARAMETER MinLot
    Taille minimale de lot (sera détectée automatiquement si non spécifiée)
    
.EXAMPLE
    .\GEN_Add-Symbol.ps1 -Symbol "XAGUSD" -AssetClass "precious_metal"
    
.EXAMPLE
    .\GEN_Add-Symbol.ps1 -Symbol "EURUSD" -AssetClass "forex" -Coefficient 2
    
.EXAMPLE
    .\GEN_Add-Symbol.ps1 -Symbol "BTCUSD" -AssetClass "crypto" -MinLot 0.01 -Coefficient 3
    
.NOTES
    Auteur: NewStratSIMPLE System
    Version: 1.0
    Date: 2025-09-19
    
    PRÉREQUIS:
    - MT5 doit être en cours d'exécution et connecté
    - Le symbole doit exister chez votre courtier MT5
    - Python doit être installé et accessible
    - Les fichiers du système doivent être présents
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="Nom exact du symbole à ajouter (ex: XAGUSD)")]
    [string]$Symbol,
    
    [Parameter(Mandatory=$true, HelpMessage="Classe d'actif: forex, crypto, index, commodity, precious_metal")]
    [ValidateSet("forex", "crypto", "index", "commodity", "precious_metal")]
    [string]$AssetClass,
    
    [Parameter(Mandatory=$false, HelpMessage="Coefficient de position (défaut: 1)")]
    [decimal]$Coefficient = 1,
    
    [Parameter(Mandatory=$false, HelpMessage="Lot minimum (sera détecté automatiquement si non spécifié)")]
    [decimal]$MinLot = 0
)

# Configuration des couleurs pour l'affichage
$Host.UI.RawUI.ForegroundColor = "White"

# Fonction pour afficher des messages colorés
function Write-ColoredMessage {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = ""
    )
    
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "Cyan"
        "Header" = "Magenta"
    }
    
    if ($colors.ContainsKey($Color)) {
        Write-Host "$Prefix$Message" -ForegroundColor $colors[$Color]
    } else {
        Write-Host "$Prefix$Message" -ForegroundColor $Color
    }
}

# Fonction pour vérifier les prérequis
function Test-Prerequisites {
    Write-ColoredMessage "🔍 Vérification des prérequis..." "Header"
    
    # Vérifier la présence des fichiers requis
    $requiredFiles = @(
        "list_symbols_capitalpoint.csv",
        "risk_config.json",
        "symbol_screener.py",
        "GEN_comprehensive_test.py"
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-ColoredMessage "❌ Fichier manquant: $file" "Error"
            return $false
        }
    }
    
    # Vérifier Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-ColoredMessage "✅ Python détecté: $pythonVersion" "Success"
        } else {
            Write-ColoredMessage "❌ Python non trouvé dans le PATH" "Error"
            return $false
        }
    } catch {
        Write-ColoredMessage "❌ Erreur lors de la vérification de Python" "Error"
        return $false
    }
    
    Write-ColoredMessage "✅ Tous les prérequis sont satisfaits" "Success"
    return $true
}

# Fonction pour ajouter le symbole à la liste principale
function Add-SymbolToList {
    param([string]$SymbolName)
    
    Write-ColoredMessage "📝 Ajout de $SymbolName à la liste des symboles..." "Info"
    
    try {
        # Lire le contenu actuel
        $currentContent = Get-Content "list_symbols_capitalpoint.csv" -Raw
        $currentContent = $currentContent.Trim()
        
        # Vérifier si le symbole existe déjà
        if ($currentContent -match "\b$SymbolName\b") {
            Write-ColoredMessage "⚠️ Le symbole $SymbolName existe déjà dans la liste" "Warning"
            return $true
        }
        
        # Ajouter le nouveau symbole
        $newContent = "$currentContent,$SymbolName"
        
        # Sauvegarder avec backup
        Copy-Item "list_symbols_capitalpoint.csv" "list_symbols_capitalpoint.csv.backup"
        Set-Content "list_symbols_capitalpoint.csv" $newContent -NoNewline
        
        Write-ColoredMessage "✅ Symbole $SymbolName ajouté à la liste" "Success"
        return $true
    } catch {
        Write-ColoredMessage "❌ Erreur lors de l'ajout du symbole: $($_.Exception.Message)" "Error"
        return $false
    }
}

# Fonction pour lancer le screening des symboles
function Start-SymbolScreening {
    Write-ColoredMessage "🔍 Lancement du screening des symboles..." "Info"
    
    try {
        $screeningOutput = python symbol_screener.py 2>&1
        
        # Vérifier si le screening a réussi
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredMessage "✅ Screening terminé avec succès" "Success"
            
            # Vérifier si notre symbole est détecté comme tradeable
            if ($screeningOutput -match "$Symbol.*Tradeable.*Quality: 100%") {
                Write-ColoredMessage "✅ $Symbol détecté comme tradeable (Qualité: 100%)" "Success"
                return $true
            } elseif ($screeningOutput -match "$Symbol.*Not available") {
                Write-ColoredMessage "❌ $Symbol n'est pas disponible chez votre courtier" "Error"
                return $false
            } else {
                Write-ColoredMessage "⚠️ Statut de $Symbol incertain, vérifiez manuellement" "Warning"
                return $true
            }
        } else {
            Write-ColoredMessage "❌ Erreur lors du screening: $screeningOutput" "Error"
            return $false
        }
    } catch {
        Write-ColoredMessage "❌ Erreur lors du screening: $($_.Exception.Message)" "Error"
        return $false
    }
}

# Fonction pour extraire les spécifications du symbole
function Get-SymbolSpecifications {
    param([string]$SymbolName)
    
    try {
        $specsFile = Get-Content "symbol_specifications.json" -Raw | ConvertFrom-Json
        $symbolSpecs = $specsFile.symbol_specifications.$SymbolName
        
        if ($symbolSpecs) {
            return @{
                min_lot = $symbolSpecs.min_lot
                available = $symbolSpecs.available
                tradeable = $symbolSpecs.tradeable
            }
        } else {
            return $null
        }
    } catch {
        Write-ColoredMessage "⚠️ Impossible de lire les spécifications pour $SymbolName" "Warning"
        return $null
    }
}

# Fonction pour mettre à jour la configuration de risque
function Update-RiskConfiguration {
    param(
        [string]$SymbolName,
        [string]$AssetClassValue,
        [decimal]$CoefficientValue,
        [decimal]$MinLotValue
    )
    
    Write-ColoredMessage "⚙️ Mise à jour de la configuration de risque..." "Info"
    
    try {
        # Lire la configuration actuelle
        $riskConfig = Get-Content "risk_config.json" -Raw | ConvertFrom-Json
        
        # Vérifier si le symbole existe déjà
        if ($riskConfig.position_coefficients.PSObject.Properties.Name -contains $SymbolName) {
            Write-ColoredMessage "⚠️ $SymbolName existe déjà dans la configuration de risque" "Warning"
            return $true
        }
        
        # Ajouter la nouvelle configuration
        $newSymbolConfig = @{
            min_lot = $MinLotValue
            coefficient = $CoefficientValue
            asset_class = $AssetClassValue
        }
        
        $riskConfig.position_coefficients | Add-Member -MemberType NoteProperty -Name $SymbolName -Value $newSymbolConfig
        
        # Sauvegarder avec backup
        Copy-Item "risk_config.json" "risk_config.json.backup"
        $riskConfig | ConvertTo-Json -Depth 10 | Set-Content "risk_config.json"
        
        Write-ColoredMessage "✅ Configuration de risque mise à jour pour $SymbolName" "Success"
        return $true
    } catch {
        Write-ColoredMessage "❌ Erreur lors de la mise à jour de la configuration: $($_.Exception.Message)" "Error"
        return $false
    }
}

# Fonction pour lancer les tests complets
function Start-ComprehensiveTest {
    Write-ColoredMessage "🧪 Lancement des tests complets..." "Info"
    
    try {
        $testOutput = python GEN_comprehensive_test.py 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredMessage "✅ Tests terminés avec succès" "Success"
            
            # Analyser les résultats pour notre symbole
            $riskApproved = $testOutput -match "$Symbol.*Approved.*Lot size"
            $orderExecuted = $testOutput -match "$Symbol.*BUY executed"
            $positionClosed = $testOutput -match "$Symbol.*Position closed successfully"
            
            Write-ColoredMessage "`n📊 RÉSULTATS POUR $Symbol :" "Header"
            
            if ($riskApproved) {
                Write-ColoredMessage "✅ Évaluation des risques : APPROUVÉ" "Success"
            } else {
                Write-ColoredMessage "❌ Évaluation des risques : ÉCHOUÉ" "Error"
            }
            
            if ($orderExecuted) {
                Write-ColoredMessage "✅ Exécution d'ordre : RÉUSSI" "Success"
            } else {
                Write-ColoredMessage "❌ Exécution d'ordre : ÉCHOUÉ" "Error"
            }
            
            if ($positionClosed) {
                Write-ColoredMessage "✅ Gestion de position : RÉUSSI" "Success"
            } else {
                Write-ColoredMessage "❌ Gestion de position : ÉCHOUÉ" "Error"
            }
            
            return ($riskApproved -and $orderExecuted -and $positionClosed)
        } else {
            Write-ColoredMessage "❌ Erreur lors des tests: $testOutput" "Error"
            return $false
        }
    } catch {
        Write-ColoredMessage "❌ Erreur lors des tests: $($_.Exception.Message)" "Error"
        return $false
    }
}

# Fonction de rollback en cas d'erreur
function Invoke-Rollback {
    Write-ColoredMessage "🔄 Rollback en cours..." "Warning"
    
    try {
        # Restaurer les fichiers de backup s'ils existent
        if (Test-Path "list_symbols_capitalpoint.csv.backup") {
            Move-Item "list_symbols_capitalpoint.csv.backup" "list_symbols_capitalpoint.csv" -Force
            Write-ColoredMessage "✅ Liste des symboles restaurée" "Success"
        }
        
        if (Test-Path "risk_config.json.backup") {
            Move-Item "risk_config.json.backup" "risk_config.json" -Force
            Write-ColoredMessage "✅ Configuration de risque restaurée" "Success"
        }
        
        Write-ColoredMessage "🔄 Rollback terminé" "Info"
    } catch {
        Write-ColoredMessage "❌ Erreur lors du rollback: $($_.Exception.Message)" "Error"
    }
}

# SCRIPT PRINCIPAL
# ================================================================================

Write-ColoredMessage @"
================================================================================
                    AJOUT AUTOMATIQUE DE SYMBOLE
================================================================================
Symbole: $Symbol
Classe d'actif: $AssetClass
Coefficient: $Coefficient
Lot minimum: $(if($MinLot -eq 0){"Auto-détection"}else{$MinLot})
================================================================================
"@ "Header"

# Étape 1: Vérification des prérequis
if (-not (Test-Prerequisites)) {
    Write-ColoredMessage "❌ Échec des prérequis. Arrêt du script." "Error"
    exit 1
}

# Étape 2: Ajout du symbole à la liste
if (-not (Add-SymbolToList -SymbolName $Symbol)) {
    Write-ColoredMessage "❌ Impossible d'ajouter le symbole. Arrêt du script." "Error"
    exit 1
}

# Étape 3: Screening des symboles
if (-not (Start-SymbolScreening)) {
    Write-ColoredMessage "❌ Échec du screening. Rollback en cours..." "Error"
    Invoke-Rollback
    exit 1
}

# Étape 4: Récupération des spécifications
$specs = Get-SymbolSpecifications -SymbolName $Symbol
if ($specs -and $specs.available -and $specs.tradeable) {
    $finalMinLot = if ($MinLot -eq 0) { $specs.min_lot } else { $MinLot }
    Write-ColoredMessage "📋 Spécifications détectées - Min Lot: $finalMinLot" "Info"
} elseif ($MinLot -gt 0) {
    $finalMinLot = $MinLot
    Write-ColoredMessage "⚠️ Utilisation du MinLot spécifié: $finalMinLot" "Warning"
} else {
    Write-ColoredMessage "❌ Impossible de déterminer le MinLot. Rollback en cours..." "Error"
    Invoke-Rollback
    exit 1
}

# Étape 5: Mise à jour de la configuration de risque
if (-not (Update-RiskConfiguration -SymbolName $Symbol -AssetClassValue $AssetClass -CoefficientValue $Coefficient -MinLotValue $finalMinLot)) {
    Write-ColoredMessage "❌ Échec de la mise à jour de configuration. Rollback en cours..." "Error"
    Invoke-Rollback
    exit 1
}

# Étape 6: Tests complets
Write-ColoredMessage "`n🧪 PHASE DE TEST - Cela peut prendre 15-20 secondes..." "Header"
if (Start-ComprehensiveTest) {
    Write-ColoredMessage @"

================================================================================
                            ✅ SUCCÈS TOTAL ! ✅
================================================================================
Le symbole $Symbol a été ajouté avec succès au système !

📊 RÉSUMÉ:
• Symbole: $Symbol
• Classe d'actif: $AssetClass  
• Coefficient: $Coefficient
• Lot minimum: $finalMinLot
• Tests: TOUS RÉUSSIS

🎯 PROCHAINES ÉTAPES:
• Le symbole est maintenant opérationnel
• Surveillez les performances initiales
• Ajustez le coefficient si nécessaire

📁 FICHIERS MODIFIÉS:
• list_symbols_capitalpoint.csv (sauvegarde créée)
• risk_config.json (sauvegarde créée)
• symbol_specifications.json (régénéré)

================================================================================
"@ "Success"
    
    # Nettoyer les fichiers de backup après succès
    Remove-Item "*.backup" -ErrorAction SilentlyContinue
    
    exit 0
} else {
    Write-ColoredMessage @"

================================================================================
                            ❌ ÉCHEC PARTIEL
================================================================================
Le symbole $Symbol a été ajouté à la configuration mais les tests ont échoué.

🔍 ACTIONS RECOMMANDÉES:
1. Vérifiez que MT5 est connecté
2. Vérifiez que le marché est ouvert pour $Symbol
3. Lancez manuellement: python GEN_comprehensive_test.py
4. Si les problèmes persistent, lancez le rollback manuel

🔄 ROLLBACK MANUEL SI NÉCESSAIRE:
• Supprimez $Symbol de list_symbols_capitalpoint.csv
• Supprimez la section $Symbol de risk_config.json
• Relancez le screening: python symbol_screener.py

================================================================================
"@ "Error"
    
    exit 1
}