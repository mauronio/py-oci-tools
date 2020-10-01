import oci
import importlib

def get_signer_from_config(config):
    # Generate the signer for the API calls using the info from the config file
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        # pass_phrase is optional and can be None
        pass_phrase=oci.config.get_config_value_or_default(
            config, "pass_phrase"),
        # private_key_content is optional and can be None
        private_key_content=config.get("key_content")
    )
    
    return signer

def get_resource_type_from_ocid(ocid):

    return ocid.split('.')[1]


class OCIClient:

    def __init__(self, config_filename = "~/.oci/config", profile_name = "DEFAULT"):

        config = oci.config.from_file(config_filename, profile_name)
        signer = get_signer_from_config(config)

        self.identity_service = oci.identity.IdentityClient(config, signer=signer)
        self.tenancy_compartment = self.identity_service.get_compartment(compartment_id=config["tenancy"])

        self.resources_API = {
            'instance': {
                'service': oci.core.ComputeClient(config, signer=signer),
                'get-method': 'get_instance',
                'tag-update-method': 'update_instance',
                'tag-updater-model-module': 'oci.core.models',
                'tag-updater-model-class': 'UpdateInstanceDetails',
                'id-parameter-name': 'instance_id',
                'details-parameter-name': 'update_instance_details'
            },
            'loadbalancer': {
                'service': oci.load_balancer.LoadBalancerClient(config, signer=signer),
                'get-method': 'get_load_balancer',
                'tag-update-method': 'update_load_balancer',
                'tag-updater-model-module': 'oci.load_balancer.models',
                'tag-updater-model-class': 'UpdateLoadBalancerDetails',
                'id-parameter-name': 'load_balancer_id',
                'details-parameter-name': 'update_load_balancer_details'
            },
            'filesystem': {
                'service': oci.file_storage.FileStorageClient(config, signer=signer),
                'get-method': 'get_file_system',
                'tag-update-method': 'update_file_system',
                'tag-updater-model-module': 'oci.file_storage.models',
                'tag-updater-model-class': 'UpdateFileSystemDetails',
                'id-parameter-name': 'file_system_id',
                'details-parameter-name': 'update_file_system_details'
            },
            'database': {
                'service': oci.database.DatabaseClient(config, signer=signer),
                'get-method': 'get_database',
                'tag-update-method': 'update_database',
                'tag-updater-model-module': 'oci.database.models',
                'tag-updater-model-class': 'UpdateDatabaseDetails',
                'id-parameter-name': 'database_id',
                'details-parameter-name': 'update_database_details'
            },
            'dbsystem': {
                'service': oci.database.DatabaseClient(config, signer=signer),
                'get-method': 'get_db_system',
                'tag-update-method': 'update_db_system',
                'tag-updater-model-module': 'oci.database.models',
                'tag-updater-model-class': 'UpdateDbSystemDetails',
                'id-parameter-name': 'db_system_id',
                'details-parameter-name': 'update_db_system_details'
            },
            'cluster': {
                'service': oci.container_engine.ContainerEngineClient(config, signer=signer),
                'get-method': 'get_cluster',
                'tag-update-method': 'update_cluster',
                'tag-updater-model-module': 'oci.container_engine.models',
                'tag-updater-model-class': 'UpdateClusterDetails',
                'id-parameter-name': 'cluster_id',
                'details-parameter-name': 'update_cluster_details'
            },
            'nodepool': {
                'service': oci.container_engine.ContainerEngineClient(config, signer=signer),
                'get-method': 'get_node_pool',
                'tag-update-method': 'update_node_pool',
                'tag-updater-model-module': 'oci.container_engine.models',
                'tag-updater-model-class': 'UpdateNodePoolDetails',
                'id-parameter-name': 'node_pool_id',
                'details-parameter-name': 'update_node_pool_details'
            }
        }

    def get_resource_by_id(self, ocid):

        resource_type = get_resource_type_from_ocid(ocid)

        resource_API = self.resources_API.get(resource_type)
        if resource_API is None:
            raise Exception('No Resource API for ' + resource_type)
        else:
            service = resource_API['service']

            try:
                get_method = getattr(service, resource_API['get-method'])
                return get_method(ocid)
            except Exception as e:
                print('Error trying to get resource by id', ocid)
                print(e)

    def set_resource_tags(self, ocid, defined_tags, freeform_tags):

        resource_type = get_resource_type_from_ocid(ocid)

        resource_API = self.resources_API.get(resource_type)
        if resource_API is None:
            raise Exception('No Resource API for ' + resource_type)
        else:
            service = resource_API['service']

            tag_update_method = getattr(service, resource_API['tag-update-method'])

            tag_updater_model_module = importlib.import_module(resource_API['tag-updater-model-module'])
            tag_updater_model_class = getattr(tag_updater_model_module, resource_API['tag-updater-model-class'])

            update_parameters = {
                resource_API['id-parameter-name']: ocid,
                resource_API['details-parameter-name']:                 
                    tag_updater_model_class(
                        defined_tags = defined_tags,
                        freeform_tags = freeform_tags
                    )
            }

            try:
                tag_update_method(**update_parameters)
            except Exception as e:
                print('Error trying to update resource for id', ocid)
                print(e)


