# ADORe Quick Start
This is a quick start guide to getting up and running with ADORe with no fuss
running the automated setup script.

For manual setup or a deeper look into getting ADORe set up please review the 
[Getting Started](getting_started/getting_started.md) guide.

To setup and configure ADORe for a first run you can run the following setup script:
```bash
bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/adore_setup.sh)
```

> **ℹ️INFO:**
> The ADORe setup script can run in non-interactive/unattended mode with:
`bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/adore_setup.sh) --headless`

This script will do the following:
 
 - Verify that your system meets the minimum requirements to run ADORe 
 - Install the system dependencies GNU Make and Docker
 - Clone ADORe to your home directory
 - Build ADORe core components

> **⚠️ WARNING:**
> The automated ADORe setup script is only supported in Ubuntu!

> **⚠️  WARNING:**
> As a general rule you should never run shell scripts from untrusted sources. 

