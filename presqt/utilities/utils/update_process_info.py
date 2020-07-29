from presqt.utilities import write_file, read_file


def update_process_info(process_info_path, total_files):
    process_info_data = read_file(process_info_path, True)
    process_info_data['total_files'] = total_files
    write_file(process_info_path, process_info_data, True)
    return

def increment_process_info(process_info_path):
    process_info_data = read_file(process_info_path, True)
    process_info_data['files_finished'] = process_info_data['files_finished'] + 1
    write_file(process_info_path, process_info_data, True)
    return