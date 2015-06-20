import pstats
pstats.Stats('profile').strip_dirs().sort_stats("cumulative").print_stats()
