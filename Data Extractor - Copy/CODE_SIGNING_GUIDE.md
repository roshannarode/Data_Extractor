# 🔐 Code Signing Guide for Data Extractor

## Overview
Digital signatures ensure your executable is trusted and hasn't been tampered with. This prevents Windows SmartScreen warnings and builds user trust.

## Prerequisites
1. **Windows SDK** - Download from Microsoft Developer site
2. **Code Signing Certificate** - See options below

## Option 1: Professional Certificate (Recommended for Distribution)

### Purchase Certificate
- **DigiCert**: ~$300-500/year
- **Sectigo**: ~$200-400/year  
- **GlobalSign**: ~$250-450/year

### Setup Steps
1. Purchase certificate and download `.pfx` file
2. Place certificate file in project folder
3. Run: `python build_exe.py --sign`
4. Enter certificate password when prompted

## Option 2: Self-Signed Certificate (Testing Only)

### Create Self-Signed Certificate
```powershell
# Install Windows SDK first, then run:
makecert -sv mykey.pvk -n "CN=YourCompanyName" mycert.cer -r
pvk2pfx -pvk mykey.pvk -spc mycert.cer -pfx mycert.pfx -po YourPassword
```

### Alternative PowerShell Method
```powershell
# Create self-signed certificate
$cert = New-SelfSignedCertificate -Subject "CN=DataExtractor" -CertStoreLocation "Cert:\CurrentUser\My" -KeyUsage DigitalSignature -Type CodeSigning

# Export to PFX file
$password = ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath ".\mycert.pfx" -Password $password
```

## Option 3: Certificate Store

### Install Certificate in Windows Store
1. Double-click certificate file → Install
2. Choose "Current User" or "Local Machine"
3. Place in "Personal" certificates store
4. Run: `python build_exe.py --sign`
5. Enter certificate subject name (e.g., "YourCompanyName")

## Usage Commands

### Build without signing
```bash
python build_exe.py
```

### Build and sign with certificate file
```bash
python build_exe.py --sign
# Will prompt for certificate password
```

### View signing help
```bash
python build_exe.py --help-signing
```

## Verification

### Check if executable is signed
```bash
# The build script automatically verifies the signature
# Or manually check:
signtool verify /pa /v dist/DataExtractor.exe
```

### View certificate details
```bash
signtool verify /pa /v /c dist/DataExtractor.exe
```

## Troubleshooting

### "signtool.exe not found"
- Install Windows SDK
- Add to PATH: `C:\Program Files (x86)\Windows Kits\10\bin\x64\`

### "No certificates were found"
- Ensure certificate is installed in correct store
- For file certificates, place `.pfx` file in project folder

### "Timestamping failed"
- Check internet connection
- Timestamp servers may be temporarily down
- Try again later

### Self-signed certificate warnings
- Self-signed certificates will still show warnings
- Users need to "Run anyway" or install your certificate as trusted
- Only professional certificates avoid warnings

## File Structure
```
Data Extractor/
├── app.py
├── build_exe.py          # Enhanced with signing
├── icon.ico
├── version_info.txt
├── mycert.pfx            # Your certificate file (if using file method)
└── dist/
    └── DataExtractor.exe # Signed executable
```

## Benefits of Code Signing
✅ **No SmartScreen warnings**  
✅ **User trust and credibility**  
✅ **Tamper detection**  
✅ **Professional appearance**  
✅ **Enterprise deployment ready**

## Cost Comparison
- **Self-signed**: Free (shows warnings)
- **Professional**: $200-500/year (no warnings)
- **EV Certificate**: $300-700/year (immediate trust, no warnings)

## Next Steps
1. Choose your certificate option
2. Install Windows SDK if needed
3. Run `python build_exe.py --sign`
4. Distribute your signed executable! 