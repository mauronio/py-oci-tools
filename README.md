# py-oci-tools
Python tools fior OCI infraestructure

# Prerequisites

* Python3
* Tenancy User OCI Credentials configuration (by default, in  ~/.oci/config file)
* Tenancy User public key included in User API Keys (OCI Console: Identity>>Users>>User Details>>API Keys)
* Terraform (for Terraform tools)

# Tools

## Blueprint Report

1) Set parameters in infra-blueprint/workspace/config.yaml file
2) Execute

   ```
   ./run-infra-blueprint.sh
   ```

3) Output spreadsheets can be found at infra-blueprint/workspace folder

## Retag resources

A "retagging project" is a specific configuration which includes:

* Infraestructure to be retagged, in the form of a json output from Terraform backend tfstate.
* Rules for declaring tag/values to ensure in the project infraestructure resources
* Rules for declaring tags to exclude from the project infraestructure resources

1) Get resource OCIDs

   a) cd to (terraform infra folder)

   b) execute

      ```
      terraform init
      ```

   c) execute

      ```
      terraform output -json > my_project_infra.json
      ```

   d) copy my_project_infra.json to workspace folder

      ```
      cp my_project_infra.json retag-resources/workspace/.
      ```

2) Edit retag-resources/workspace/config.yaml and include "my_project" details

3) Execute and confirm changes when asked (default form)

   ```
   ./run-retag-resources
   Process plan saved to /default/folder//workspace
   Are you sure you want to apply the plan? (yes/no):
   ```

   You can specify forced mode, a plan only run (no changes to infraestructure), or a different workspace folder:

   ```
   ./run-retag-resources.sh -h
   usage: controller.py [-h] [-p] [-f] [-w WORKSPACE_FOLDER]

   optional arguments:
   -h, --help           show this help message and exit
   -p, --plan           only build plan file in workspace
   -f, --force          do not ask for confirmation before apply
   -w WORKSPACE_FOLDER, --workspace-folder WORKSPACE_FOLDER
                        set workspace folder. 
   ```

4) Output files can be found at retag-resources/workspace folder
