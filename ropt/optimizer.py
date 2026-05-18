from .means import normal_weighted_arithimetic_mean

def pair_iterator(direction_map):
    """
    Generates pairs of indices from the direction_map for optimization.
    Parameters:
    direction_map : list
        A list of indices representing the directions.
    Returns: generator
        A generator that yields pairs of indices from the direction_map.
    """
    while True:
        for n in ((direction_map[i],direction_map[j]) for j in range(len(direction_map)) for i in range(j)):
            yield n
            
def optimization(normal_data, quality_indicator, coef=None, direction_map=None,
                        dstep = 0.01, limit_dquality = 0.0001, limit_nstep = 5000,
                        upper_limits = None, lower_limits = None,
                        mu_x = normal_weighted_arithimetic_mean
                       ):
    """
    Performs optimization on the given normalized data using specified quality indicator and parameters.
    Parameters:
    normal_data : DataFrame
        A DataFrame containing the normalized data to be optimized.
    quality_indicator : function
        A function that evaluates the quality of the data.
    coef : list, optional
        A list of coefficients for the aggregation. If None, defaults to equal weights.
    direction_map : list, optional
        A list of indices representing the directions for optimization. If None, defaults to all indices.
    dstep : float, optional
        The step size for the optimization. Default is 0.01.
    limit_dquality : float, optional
        The threshold for the improvement to continue optimization. Default is 0.0001.
    limit_nstep : int, optional
        The maximum number of optimization steps. Default is 5000.
    upper_limits : list, optional
        A list of upper limits for the coefficients. If None, defaults to 1 for each coefficient.
    lower_limits : list, optional
        A list of lower limits for the coefficients. If None, defaults to 0 for each coefficient.
    mu_x : function, optional
        A function that aggregates the objects of the data with the coeficients. Default is normal_weighted_arithimetic_mean.
    Returns: list
        A list of optimized coefficients.
    """
    if upper_limits is None:
        upper_limits = [1 for _ in range(normal_data.shape[1])]
    if lower_limits is None:
        lower_limits = [0 for _ in range(normal_data.shape[1])]
    if direction_map is None:
        direction_map = [i for i in range(normal_data.shape[1])]
        
    pairs_gen = pair_iterator(direction_map)
    n_directions = (len(direction_map) * (len(direction_map)-1)) / 2
    pair = next(pairs_gen)
    
    covered_directions = 0
    n_step = 0
    
    if coef is None:
        coef = [1/normal_data.shape[1] for _ in range(normal_data.shape[1])]
    ci = normal_data.apply(lambda row: mu_x(coef, row), axis=1)
    quality = quality_indicator(ci)
    old_quality = 2 * limit_dquality + quality
    
    while n_step < limit_nstep and covered_directions < n_directions:
        updated = False
        actual_dstep=dstep
        if coef[pair[0]] + actual_dstep > upper_limits[pair[0]]:
            actual_dstep = upper_limits[pair[0]] - coef[pair[0]]
        if coef[pair[1]] - actual_dstep < lower_limits[pair[1]]:
            actual_dstep = coef[pair[1]] - lower_limits[pair[1]]
        # print(n_step, pair)
        # print(quality)
        # print(covered_directions, n_directions)
        
        if actual_dstep>0:
            new_coef = coef.copy()
            new_coef[pair[0]] += actual_dstep
            new_coef[pair[1]] -= actual_dstep
            
            ci = normal_data.apply(lambda row: mu_x(new_coef, row), axis=1)
            new_quality = quality_indicator(ci)
            if new_quality > quality:
                quality = new_quality
                coef = new_coef
                updated = True

        # print('coef')
        # print(coef)
        actual_dstep=dstep
        if coef[pair[1]] + actual_dstep > upper_limits[pair[1]]:
            actual_dstep = upper_limits[pair[1]] - coef[pair[1]]
        if coef[pair[0]] - actual_dstep < lower_limits[pair[0]]:
            actual_dstep = coef[pair[0]] - lower_limits[pair[0]]
            
        if not updated and actual_dstep>0:
            new_coef = coef.copy()
            new_coef[pair[0]] -= actual_dstep
            new_coef[pair[1]] += actual_dstep
            
            ci = normal_data.apply(lambda row: mu_x(new_coef, row), axis=1)
            new_quality = quality_indicator(ci)
            if new_quality > quality:
                quality = new_quality
                coef = new_coef
                
        if limit_dquality <= abs(quality - old_quality):
            covered_directions = 0
        else:
            covered_directions += 1
    
        old_quality = quality
        pair = next(pairs_gen)
        n_step += 1
        
    return coef

'''
def optimization_graphed(normal_data, quality_indicator, coef=None,
                        dstep = 0.01, limit_dquality = 0.0001, limit_nstep = 5000,
                        upper_limits = None, lower_limits = None,
                        mu_x = normal_weighted_arithimetic_mean
                       ):
    if upper_limits is None:
        upper_limits = [1 for _ in range(normal_data.shape[1])]
    if lower_limits is None:
        lower_limits = [0 for _ in range(normal_data.shape[1])]
    
    pairs_gen = pair_iterator(normal_data.shape[1])
    n_directions = (normal_data.shape[1] * (normal_data.shape[1]-1)) / 2
    pair = next(pairs_gen)
    
        # defining counters
    covered_directions = 0
    n_step = 0
    
        # defining permanent variables
    if coef is None:
        coef = [1/normal_data.shape[1] for _ in range(normal_data.shape[1])]        
    ci = normal_data.apply(lambda row: mu_x(coef, row), axis=1)
    quality = quality_indicator(ci)
    old_quality = 2 * limit_dquality + quality # makes it out of bounds of the verification for first step
    
        # FOR GRAPH / DEBUG
    # print((n_directions, quality))
    # print(abs(quality - old_quality))
    # print(limit_dquality)
    # print(abs(quality - old_quality) <= limit_dquality)
    
    memory_y = [quality]
    memory_x = [0]
    ntests = 0
    memory_test = [0]
    updated = False
    
        # Function loop
    while n_step < limit_nstep and covered_directions < n_directions: # limit_dquality <= abs(quality - old_quality):
            # FOR GRAPH / DEBUG
        # print(n_step, pair)
        # print(quality, coef)
        # print(covered_directions, n_directions)
        
        # test positive
        updated = False
        actual_dstep=dstep
        if coef[pair[0]] + actual_dstep > upper_limits[pair[0]]:
            actual_dstep = upper_limits[pair[0]] - coef[pair[0]]
        if coef[pair[1]] - actual_dstep < lower_limits[pair[1]]:
            actual_dstep = coef[pair[1]] - lower_limits[pair[1]]
            
        if actual_dstep>0:
                # update coefs
            new_coef = coef.copy()
            new_coef[pair[0]] += actual_dstep
            new_coef[pair[1]] -= actual_dstep
                # calculate new index quality
            ci = normal_data.apply(lambda row: mu_x(new_coef, row), axis=1)
            new_quality = quality_indicator(ci)
                # FOR GRAPH / DEBUG
            ntests += 1
            # print('positive', old_quality, quality, new_quality)
                # update coef if better
            if new_quality > quality:
                quality = new_quality
                coef = new_coef
                updated = True
                    # FOR GRAPH / DEBUG
                memory_y.append(quality)
                memory_x.append(n_step+1)
                memory_test.append(ntests)
        # test negative      
        actual_dstep=dstep
        if coef[pair[1]] + actual_dstep > upper_limits[pair[1]]:
            actual_dstep = upper_limits[pair[1]] - coef[pair[1]]
        if coef[pair[0]] - actual_dstep < lower_limits[pair[0]]:
            actual_dstep = coef[pair[0]] - lower_limits[pair[0]]
            
        if not updated and actual_dstep>0:
                # update coefs
            new_coef = coef.copy()
            new_coef[pair[0]] -= actual_dstep
            new_coef[pair[1]] += actual_dstep
                # calculate new index quality
            ci = normal_data.apply(lambda row: mu_x(new_coef, row), axis=1)
            new_quality = quality_indicator(ci)
                # FOR GRAPH / DEBUG
            ntests += 1
            # print('negative', old_quality, quality, new_quality)
                # update coef if better
            if new_quality > quality:
                quality = new_quality
                coef = new_coef
                    # FOR GRAPH / DEBUG
                memory_y.append(quality)
                memory_x.append(n_step+1)
                memory_test.append(ntests)
    
        # Check if enough improvement were found.
        if limit_dquality <= abs(quality - old_quality):
            covered_directions = 0
        else:
            # print('no improvement')
                # counts how many directions have failed for finishing
            covered_directions += 1
    
        # move to the next step
        old_quality = quality
        pair = next(pairs_gen)
        n_step += 1
        
        # FOR GRAPH / DEBUG
    if not updated:
        memory_y.append(quality)
        memory_x.append(n_step+1)
        memory_test.append(ntests)
        
    return (coef, memory_y, memory_x, memory_test)
'''