import hashlib
import os

from django.core.management import BaseCommand

from presqt.utilities import write_file, read_file, get_dictionary_from_list


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ##### Get Input From User #####
        while True:
            target_name = input('Enter target name (use underscores not spaces): ').lower()
            if set('[~! @#$%^&*()+{}":;[],.<>`=+-\']+$\\').intersection(target_name):
                print("Target name can't contain special characters or spaces")
            else:
                break
        human_readable_target_name = input('Enter human readable target name (format however): ')

        while True:
            resource_collection = input('Does your target support the Resource Collection endpoint? (Y or N): ')
            if resource_collection not in ['Y', 'y', 'N', 'n']:
                print('Must input Y or N')
            else:
                if resource_collection in ['Y', 'y']:
                    resource_collection = True
                else:
                    resource_collection = False
                break

        while True:
            resource_detail = input('Does your target support the Resource Detail endpoint? (Y or N): ')
            if resource_detail not in ['Y', 'y', 'N', 'n']:
                print('Must input Y or N')
            else:
                if resource_detail in ['Y', 'y']:
                    resource_detail = True
                else:
                    resource_detail = False
                break

        while True:
            resource_download = input('Does your target support the Resource Download endpoint? (Y or N): ')
            if resource_download not in ['Y', 'y', 'N', 'n']:
                print('Must input Y or N')
            else:
                if resource_download in ['Y', 'y']:
                    resource_download = True
                else:
                    resource_download = False
                break

        while True:
            resource_upload = input('Does your target support the Resource Upload endpoint? (Y or N): ')
            if resource_upload not in ['Y', 'y', 'N', 'n']:
                print('Must input Y or N')
            else:
                if resource_upload in ['Y', 'y']:
                    resource_upload = True
                else:
                    resource_upload = False
                break
        
        while True:
            resource_transfer = input('Does your target support the Resource Transfer endpoint? (Y or N): ')
            if resource_transfer not in ['Y', 'y', 'N', 'n']:
                print('Must input Y or N')
            else:
                if resource_transfer in ['Y', 'y']:
                    resource_transfer = True
                else:
                    resource_transfer = False
                break

        while True:
            hash_algorithms = input('Enter your supported hash algorithms (comma separated list with no spaces): ')
            if ' ' in hash_algorithms:
                print("Input can't contain spaces")
                continue
            hash_algorithms = hash_algorithms.split(',')
            for hash_algorithm in hash_algorithms:
                if hash_algorithm not in hashlib.algorithms_available:
                    print('{} is not supported by the hashlib Python library'.format(hash_algorithm))
                    break
            else:
                break

        ##### Check if target exists in targets.json #####
        data = read_file('presqt/targets.json', True)
        if get_dictionary_from_list(data, 'name', target_name):
            print('Error! Target, {}, already exists in targets.json!'.format(target_name))
            return

        ##### Make Target Directory #####
        target_directory = 'presqt/targets/{}/'.format(target_name)
        try:
            os.makedirs(os.path.dirname(target_directory))
            print('Directory created: {}'.format(target_directory))
        except FileExistsError:
            print('Error! Target directory already exists!')
            return
        else:
            open('{}{}'.format(target_directory, '__init__.py'), 'a').close()

        ##### Make Target Function Directory #####
        target_function_dir = '{}{}/'.format(target_directory, 'functions')
        os.makedirs(os.path.dirname(target_function_dir))
        print('Directory created: {}'.format(target_function_dir))
        open('{}{}'.format(target_function_dir, '__init__.py'), 'a').close()
        print('File created: {}'.format(target_function_dir))

        ##### Make Target Action Files ####
        target_functions = {}
        if resource_collection or resource_detail:
            with open('{}fetch.py'.format(target_function_dir), 'w') as file:
                target_functions['fetch'] = {}

                if resource_collection:
                    resource_collection_function ='{}_fetch_resources'.format(target_name)
                    target_functions['fetch']['{}_resource_collection'.format(target_name)] = resource_collection_function

                    file.write('def {}(token):\n\tpass'.format(resource_collection_function))
                    if resource_detail:
                        file.write('\n\n')

                if resource_detail:
                    resource_detail_function = '{}_fetch_resource'.format(target_name)
                    target_functions['fetch']['{}_resource_detail'.format(target_name)] = resource_detail_function
                    file.write('def {}(token, resource_id):\n\tpass'.format(resource_detail_function))

                print('File created: {}fetch.py'.format(target_function_dir))

        if resource_download:
            with open('{}download.py'.format(target_function_dir), 'w') as file:
                resource_download_function ='{}_download_resource'.format(target_name)
                target_functions['download'] = {'{}_resource_download'.format(target_name): resource_download_function}
                file.write('def {}(token, resource_id):\n\tpass'.format(resource_download_function))
                print('File created: {}download.py'.format(target_function_dir))

        if resource_upload:
            with open('{}upload.py'.format(target_function_dir), 'w') as file:
                resource_upload_function = '{}_upload_resource'.format(target_name)
                target_functions['upload'] = {'{}_resource_upload'.format(target_name): resource_upload_function}
                file.write('def {}(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action):\n\tpass'.format(resource_upload_function))
                print('File created: {}upload.py'.format(target_function_dir))

        ##### Write to function_router.py #####
        with open('presqt/api_v1/utilities/utils/function_router.py', 'a') as file:
            if target_functions:
                file.write('\n')

            for file_name, file_name_dict in target_functions.items():
                for variable_name, function_name in file_name_dict.items():
                    file.write('    {} = {}\n'.format(variable_name, function_name))

        with open('presqt/api_v1/utilities/utils/function_router.py', 'r+') as file:
            content = file.read()
            file.seek(0, 0)

            new_imports = ''
            for file_name, file_name_dict in target_functions.items():
                new_imports += 'from presqt.targets.{}.functions.{} import {}\n'.format(target_name, file_name, ', '.join(file_name_dict.values()))

            file.write(new_imports + content)
        print('File updated: presqt/api_v1/utilities/utils/function_router.py')

        ##### Write to targets.json #####
        target_dict = {
            "name": target_name,
            "readable_name": human_readable_target_name,
            "supported_actions": {
                "resource_collection": resource_collection,
                "resource_detail": resource_detail,
                "resource_download": resource_download,
                "resource_upload": resource_upload,
                "resource_transfer": resource_transfer
            },
            "supported_hash_algorithms": hash_algorithms
        }

        data = read_file('presqt/targets.json', True)
        data.append(target_dict)
        write_file('presqt/targets.json', data, True)
        print('File updated: presqt/targets.json')