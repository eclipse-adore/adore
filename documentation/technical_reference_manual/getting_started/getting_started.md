<!--
********************************************************************************
* Copyright (C) 2017-2020 German Aerospace Center (DLR). 
* Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
*
* This program and the accompanying materials are made available under the 
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* SPDX-License-Identifier: EPL-2.0 
*
* Contributors: 
*   Andrew Koerner
*   Björn Bahn
********************************************************************************
-->
This guide will help you get your system set up and configured to run ADORe.

1. First review the [System Requirements 🔗](system_requirements.md). 

2. Next review the [Prerequisites 🔗](prerequisites.md) 

## Cloning the ADORe repository
> **ℹ️INFO:**
> By default this guide assumes you have ssh keys configured for GitHub your GitHub account.
> For help on configuring your ssh keys visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account


```bash
git clone git@github.com:DLR-TS/adore.git
cd adore
git submodule update --init --recursive
```

> **⚠️ WARNING:** Failing to update and recursively clone the submodules will result in build failures!

> **ℹ️INFO:** If you would rather clone ADORe anonymously over https please review the [Anonymous Cloning 🔗](../system_and_development/anonymous_cloning.md) guide.

## Building ADORe
> **⚠️ WARNING:**
> To use ADORe you must have Docker, and GNU Make installed and configured for you user.

Build the ADORe Docker context, known as ADORe CLI, in the base of the ADORe repository:
```bash
make build
```

> **ℹ️INFO:** On first run of the ADORe CLI the entire system will be built. 
> Initial build can take 10-15 minutes depending on system and network.

## Running ADORe
After cloning and satisfying all system prerequisites and building ADORe
you can start the ADORe CLI interactive shell docker context.
To do this navigate to the root of the ADORe repository directory
and run the following command:
```bash
make cli
```

> **✅ SUCCESS:**
> If you are greeted with the following ADORe CLI car then you have successfully setup ADORe:
```
            ____ 
         __/  |_\__
        |           -. 
  ......'-(_)---(_)--' 
```


> **✅ INFO:** Next steps...
