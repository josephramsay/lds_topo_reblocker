# BDE DEVELOPMENT SUPPORT

## Description
Development support for BDE processor tools. Provides scripts and configuration
for deployment of BDE processor tools from source code to _~/apps_ directory for 
development and debugging.

Use only for development!

## Features
**Scripts**
* **dev-liblinz-bde-perl**    - deploy linz-bde-perl from source code
* **dev-liblinz-utils-perl**  - deploy linz-utils-perl from source code
* **dev-liblinz-bde-copy**    - deploy linz-bde-copy from source code
* **dev-linz-bde-uploader**   - deploy linz-bde-uploader from source code and
                                create development database

## Usage

Change into the project source code directory that is mounted on your local machine. e.g:

```
cd /vagrant-dev/linz_bde_uploader
```

Then install the source code for that package with the development install script:

```
dev-linz-bde-uploader
```

See [README.md](../../../README.md#development) for instructions on how to setup the local machine mount point.
