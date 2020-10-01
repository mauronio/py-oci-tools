import oci_utils
import os
import yaml
import json
import sys
import copy
import argparse
import terraform_utils

DEFAULT_WORK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace'))
CONFIG_FILE_NAME = 'config.yaml'

def get_config(working_path):

    config = None

    with open(os.path.join(working_path, CONFIG_FILE_NAME), 'r') as f:
        config = yaml.safe_load(f)

    return config

def get_new_resource_tags(project_settings, current_resource_defined_tags, current_resource_freeform_tags):

    new_resource_defined_tags = copy.deepcopy(current_resource_defined_tags)
    new_resource_freeform_tags = copy.deepcopy(current_resource_freeform_tags)

    ensure_tags = project_settings.get('ensure-tags')
    if not ensure_tags is None:

        ensure_defined_tags = ensure_tags.get('defined-tags')
        if not ensure_defined_tags is None:
            for namespace_key in ensure_defined_tags.keys():
                new_namespace = new_resource_defined_tags.get(namespace_key)
                if new_namespace is None:
                    new_resource_defined_tags[namespace_key] = {}
                for key, value in ensure_defined_tags[namespace_key].items():
                    new_resource_defined_tags[namespace_key][key] = value

        ensure_freeform_tags = ensure_tags.get('freeform-tags')
        if not ensure_freeform_tags is None:
            for key, value in ensure_freeform_tags.items():
                new_resource_freeform_tags[key] = value

    exclude_tags = project_settings.get('exclude-tags')
    if not exclude_tags is None:

        exclude_defined_tags = exclude_tags.get('defined-tags')
        if not exclude_defined_tags is None:
            for namespace_key in exclude_defined_tags.keys():
                new_namespace = new_resource_defined_tags.get(namespace_key)
                if not new_namespace is None:
                    for key in exclude_defined_tags[namespace_key]:
                        if not new_resource_defined_tags[namespace_key].get(key) is None:
                            del new_resource_defined_tags[namespace_key][key]

        freeform_tags = exclude_tags.get('freeform-tags')
        if not freeform_tags is None:
            for key in freeform_tags:
                if not new_resource_freeform_tags.get(key) is None:
                    del new_resource_freeform_tags[key]


    return new_resource_defined_tags, new_resource_freeform_tags

def plan_project_resource_item(project_settings, oci_client, resource_ocid):

    resource = oci_client.get_resource_by_id(resource_ocid)

    if not resource is None:

        try:
            current_resource_defined_tags = resource.data.defined_tags
            current_resource_freeform_tags = resource.data.freeform_tags
        except:
            return None

        new_resource_defined_tags, new_resource_freeform_tags = get_new_resource_tags(project_settings, current_resource_defined_tags, current_resource_freeform_tags)

        return {
                'resource-name': resource.data.display_name,
                'resource-id': resource.data.id,
                'resource-compartment-id': resource.data.compartment_id,
                'current-tags': {'defined_tags': current_resource_defined_tags, 'freeform_tags': current_resource_freeform_tags},
                'new-tags': {'defined_tags': new_resource_defined_tags, 'freeform_tags': new_resource_freeform_tags}
        }

    else:

        return None

def plan_project_resource_data(project_settings, oci_client, project_resource_item_data):

    result = []

    if isinstance(project_resource_item_data, dict):
        resource_ocid = project_resource_item_data['id']
        project_resource_item_plan = plan_project_resource_item(project_settings, oci_client, resource_ocid)
        if not project_resource_item_plan is None:
            result.append(project_resource_item_plan)
    elif isinstance(project_resource_item_data, list):
        for item in project_resource_item_data:
            if isinstance(item, dict):
                resource_ocid = item['id']
                project_resource_item_plan = plan_project_resource_item(project_settings, oci_client, resource_ocid)
                if not project_resource_item_plan is None:
                    result.append(project_resource_item_plan)

    return result

def plan_project(base_path, oci_client, config, project_name):

    result = {
        'project-name': project_name,
        'resources': {}
    }

    project_settings = config[project_name + '-settings']
    project_resources_file_name = project_settings['resources-file-name']
    project_resources_terraform_path = project_settings['resources-terraform-path']

    if project_resources_terraform_path:
        terraform_project_resources = terraform_utils.get_output(project_resources_terraform_path)
        with open(os.path.join(base_path, project_resources_file_name), 'w') as f:
            f.write(json.dumps(terraform_project_resources, indent=4))

    with open(os.path.join(base_path, project_resources_file_name)) as f:
        project_resources = json.loads(f.read())

    for resource_category in project_resources.keys():
        if not project_resources[resource_category].get('value') is None:
            project_resource_item_data = project_resources[resource_category]['value']
            project_resource_data_plan = plan_project_resource_data(project_settings, oci_client, project_resource_item_data)
            if project_resource_data_plan:
                result['resources'][resource_category] = project_resource_data_plan

    return result

def plan_process(base_path):

    oci_client = oci_utils.OCIClient()

    config = get_config(base_path)

    process_plan = []

    for project_name in config['projects']:
        print('Creating plan for', project_name, '...')
        process_plan.append(plan_project(base_path, oci_client, config, project_name))

    process_plan_full_filename = os.path.join(base_path, 'process-plan.json')
    print('Process plan saved to', process_plan_full_filename)

    with open(process_plan_full_filename, 'w') as f:
        f.write(json.dumps(process_plan, indent=4))
 
    return process_plan

def execute_process(process_plan):

    oci_client = oci_utils.OCIClient()

    for project in process_plan:

        project_name = project['project-name']
        print('Executing plan for', project_name)

        for resource_type, resources_list in project['resources'].items(): 
            for resource_data in resources_list:
                resource_name = resource_data['resource-name']
                resource_id = resource_data['resource-id']
                new_tags = resource_data['new-tags']
                print('Processing', resource_type, resource_name, '...')

                oci_client.set_resource_tags(resource_id, new_tags['defined_tags'], new_tags['freeform_tags'])

        print('Done')


def confirm_user():
    check = str(input("Are you sure you want to apply the plan? (yes/no): ")).lower().strip()
    try:
        if check == 'yes':
            return True
        elif check == 'no':
            return False
        else:
            print('Please answer yes or no')
            return confirm_user()
    except Exception as error:
        print("Please enter valid inputs")
        print(error)
        return confirm_user()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--plan', help='only build plan file in workspace', action="store_true")
    parser.add_argument('-f', '--force', help='do not ask for confirmation before apply', action="store_true")
    parser.add_argument('-w', '--workspace-folder', help='set workspace folder. By default is ' + DEFAULT_WORK_PATH, default = DEFAULT_WORK_PATH)

    args=parser.parse_args()

    process_plan = plan_process(base_path=args.workspace_folder)

    do_process = True

    if args.plan:
        do_process = False

    if not args.plan and not args.force:
        do_process = confirm_user()

    if do_process:
        execute_process(process_plan)

