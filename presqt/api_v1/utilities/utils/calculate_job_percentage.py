def calculate_job_percentage(total_files, files_finished):
    """
    Do some maths to calculate the job percentage :)

    Parameters
    ----------
    total_files: int
        Total number of files for a job
    files_finished: int
        Files finished for a job

    Returns
    -------
    An int representation of the job percentage
    """
    job_percentage = 0
    if total_files != 0 and files_finished != 0:
        job_percentage = round(files_finished / total_files * 100)
        # Little bit of a hack here, the front end doesn't build resources as fast as they are
        # returned so to get around the FE hanging on 100% for a few seconds, we'll display 99.
        if job_percentage == 100:
            job_percentage = 99
    return job_percentage