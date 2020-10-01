from python_terraform import *

def get_output(terraform_path):

    print('Getting terraform outputs from ', terraform_path, '...')
    tf = Terraform(working_dir=terraform_path)
    tf.init()
    return tf.output()
