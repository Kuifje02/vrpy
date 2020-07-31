import examples.benchmarks.run.run as run


def test_csvWriter():
    #Specify absolute paths
    try:
        path_instance_data = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/data/cvrp/'
        path_results_folder = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/run/'
        run.iterate_through_instances(path_instance_data=path_instance_data,
                                      path_results_folder=path_results_folder,
                                      multi_thread=True)
    except:
        "Error"
