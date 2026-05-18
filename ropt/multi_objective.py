from .optimizer import optimization
from .optimization import NormalizeIndicator, MultiObjective, ImportanceIndicator
from .means import weighted_arithimetic_mean

def _fix_lower(coef, upper, lower, n, ignore):
    extra = 0
    for i, (val,ll) in enumerate(zip(coef,lower)):
        if val < ll:
            extra += ll-val
            ignore.add(i)

    coef = [ll if i in ignore else val-extra/(len(coef)-len(ignore)) for i, (val,ll) in enumerate(zip(coef,lower))]
    # print(('l',n,extra,ignore,['%.3f'%val for val in coef]))
    if n>0 and any((coef<ll for coef, ll in zip(coef,lower))):
        return _fix_lower(coef, upper, lower,n-1,ignore)
    if n>0 and any((coef>ul for coef, ul in zip(coef,upper))):
        return _fix_upper(coef, upper, lower,n-1,set())
    return coef

def _fix_upper(coef, upper, lower, n, ignore):
    extra = 0
    for i, (val,ul) in enumerate(zip(coef,upper)):
        if val > ul:
            extra += val-ul
            ignore.add(i)

    coef = [ul if i in ignore else val+extra/(len(coef)-len(ignore)) for i, (val,ul) in enumerate(zip(coef,upper))]
    # print(('u',n,extra,ignore,['%.3f'%val for val in coef]))
    if n>0 and any((coef>ul for coef, ul in zip(coef,upper))):
        return _fix_upper(coef, upper, lower,n-1,ignore)
    if n>0 and any((coef<ll for coef, ll in zip(coef,lower))):
        return _fix_lower(coef, upper, lower,n-1,set())
    return coef

def fix_coef(coef, upper, lower, n=1000):
    """
    Fixes the coefficients to ensure they are within the specified upper and lower limits.
    Parameters:
    coef : list
        Coefficients to be fixed.
    upper : list
        Upper limits for the coefficients.
    lower : list
        Lower limits for the coefficients.
    n : int, optional
        Maximum number of iterations to fix the coefficients. Default is 1000.
    Returns: list
        Fixed coefficients that are within the specified upper and lower limits.
    """
    return _fix_upper(coef,upper,lower,n,set())

def find_normal_indicators(normal_data, indicators,
                            mu_x, dstep, coef,
                            limit_dquality, limit_nstep,
                            upper_limits, lower_limits,
                            importance_factors,
                            out_min, out_max,
                            ans_min, ans_max
                          ):

    """
    Finds normal indicators for the multi criteria method.
    Parameters:
    normal_data : DataFrame
        A pandas DataFrame containing the normalized data for the optimization.
    indicators : list
        A list of indicator functions to be normalized.
    mu_x : function
        Aggregate function that combines each line of the data with the supposed answer.
    dstep : float
        Step size for the optimization process.
    coef : list
        Initial coefficients for the optimization.
    limit_dquality : float
        Limit for the quality of the distribution.
    limit_nstep : int
        Maximum number of steps for the optimization process.
    upper_limits : list
        Upper limits for the coefficients.
    lower_limits : list
        Lower limits for the coefficients.
    importance_factors : list, optional
        A list of importance factors for each indicator. If None, defaults to 1 for all indicators.
    out_min : list
        List to store the minimum values of the indicators.
    out_max : list
        List to store the maximum values of the indicators.
    Returns: tuple
        A tuple containing:
        - A list of normalized indicators.
        - A list of possible starting coefficients for the optimization.
    Parametric returns:
    out_max : list
        List containing the maximum values of the indicators after optimization.
    out_min : list
        List containing the minimum values of the indicators after optimization.
    """
    # print(importance_factors)
    if importance_factors is None:
        importance_factors = [1 for _ in indicators]
    # print(importance_factors)
        
    print("Finding worst solution")
    coefs = [
        optimization(
            normal_data, lambda ci: -indicator(ci),
            mu_x=mu_x, dstep=dstep, coef=coef,
            limit_dquality=limit_dquality, limit_nstep=limit_nstep,
            upper_limits=upper_limits, lower_limits=lower_limits
        ) for indicator in indicators
    ]
    for lst in coefs: print(['%.3f'%val for val in lst])
        
    print("Calculating worst qualities")
    cis = [normal_data.apply(lambda row: mu_x(coef, row), axis=1) for coef in coefs]
    worst_qualities = [
        [
            indicator(ci)
            for ci in cis
        ] for indicator in indicators
    ]
    for lst in worst_qualities: print(lst)
    worst_qualities = [min(quality) for quality in worst_qualities]
    
    #saving worst data
    if out_min is not None:
        if len(out_min) == 0:
            for quality in worst_qualities:
                out_min.append(quality)
        else:
            for i, quality in enumerate(worst_qualities):
                if quality < out_min[i]:
                    out_min[i] = quality
            worst_qualities = list(out_min)
    if ans_min is not None:
        if len(ans_min) == 0:
            for answer in coefs:
                ans_min.append(answer)
        else:
            for i, (quality, answer) in enumerate(zip(worst_qualities,coefs)):
                if quality <= out_min[i]:
                    ans_min[i] = answer
    
    print("Finding best solution")
    coefs = [
        optimization(
            normal_data, indicator,
            mu_x=mu_x, dstep=dstep, coef=coef,
            limit_dquality=limit_dquality, limit_nstep=limit_nstep,
            upper_limits=upper_limits, lower_limits=lower_limits
        ) for indicator in indicators
    ]
    for lst in coefs: print(['%.3f'%val for val in lst])

    print("Calculating best qualities")
    cis = [normal_data.apply(lambda row: mu_x(coef, row), axis=1) for coef in coefs]
    best_qualities = [
        [
            indicator(ci)
            for ci in cis
        ] for indicator in indicators
    ]
    for lst in best_qualities: print(lst)
    best_qualities = [max(quality) for quality in best_qualities]

    #saving max data
    if out_max is not None:
        if len(out_max) == 0:
            for quality in best_qualities:
                out_max.append(quality)
        else:
            for i, quality in enumerate(best_qualities):
                if quality > out_max[i]:
                    out_max[i] = quality
            best_qualities = list(out_max)
    if ans_max is not None:
        if len(ans_max) == 0:
            for answer in coefs:
                ans_max.append(answer)
        else:
            for i, (quality, answer) in enumerate(zip(best_qualities,coefs)):
                if quality >= out_max[i]:
                    ans_max[i] = answer
    
    # print("Normalizing indicators")
    normal_indicators = [
        NormalizeIndicator(indicator, b_quality, w_quality)
        for indicator, b_quality, w_quality in zip(indicators, best_qualities, worst_qualities)
    ]
    # print(normal_indicators)
    # print(importance_factors)
    # print("Applying importance factors")
    normal_indicators = [
        ((ImportanceIndicator(indicator, factor)) if (factor != 1) else (indicator))
        for indicator, factor in zip(normal_indicators, importance_factors)
    ]
    # print(normal_indicators)
    return normal_indicators, coefs

def optimize_best_2(best_coefs, normal_data,
                    limit_mdiff, mu_x, dstep,
                    limit_nquality, limit_nstep,
                    upper_limits, lower_limits,
                    chooser
                   ):
    """
    Optimizes the best coefficients for the multi-objective optimization.
    Parameters:
    best_coefs : list
        A list of the best coefficients found during the optimization.
    normal_data : DataFrame
        A DataFrame containing the normalized data for the optimization.
    limit_mdiff : float
        Limit for the difference between the best coefficients on the multi criteria optimization.
    mu_x : function
        Aggregate function that combines each line of the data with the supposed answer.
    dstep : float
        Step size for the optimization process.
    limit_nquality : float
        Limit or the difference between the best coefficients on the mono objective optimization.
    limit_nstep : int
        Maximum number of steps for the mono optimization process.
    upper_limits : list
        Upper limits for the coefficients.
    lower_limits : list
        Lower limits for the coefficients.
    chooser : function
        Function to choose the best coefficients.
    Returns: list
        A list with 2 optimized coefficients.
    """
    # print("Calculating normal qualities")
    cis = [normal_data.apply(lambda row: mu_x(coef, row), axis=1) for coef in best_coefs]
    best_qualities = [(i, chooser(ci)) for i, ci in enumerate(cis)]
    best_qualities.sort(key=lambda x: x[1], reverse=True)
    # for lst in best_qualities: print(['%.3f'%val for val in lst])
    # best_qualities = [x[0] for x in best_qualities[:2]]

    # print("Optimizing starting coeficients")
    new_coefs = [
        optimization(
                normal_data, chooser, 
                coef=best_coefs[quality[0]], mu_x=mu_x, dstep=dstep,
                limit_dquality=limit_nquality, limit_nstep=limit_nstep,
                upper_limits=upper_limits, lower_limits=lower_limits
            ) for quality in best_qualities[:2]
    ]
    
    # print("Finding different points")
    choosen=1
    while all((abs(c1-c0)<limit_mdiff for c0,c1 in zip(new_coefs[0],new_coefs[1]))):
        choosen += 1
        if choosen==len(best_coefs):
            break
        new_coefs[1] = optimization(
            normal_data, chooser,
            coef=best_coefs[best_qualities[choosen][0]], mu_x=mu_x, dstep=dstep,
            limit_dquality=limit_nquality, limit_nstep=limit_nstep,
            upper_limits=upper_limits, lower_limits=lower_limits
        )
        
    if choosen == len(best_coefs):
        return [new_coefs[0]]
    return new_coefs

def making_the_line(coefs, upper_limits, lower_limits):
    """
    Creates a line between the two best coefficients.
    This function generates three points:
    One before the first point, one after the first point and one in between both points.
    All points are at the same distance from the closest point up to the limits provided.
    Parameters:
    coefs : list
        A list of two coefficients to create the line between.
    upper_limits : list
        Upper limits for the coefficients.
    lower_limits : list
        Lower limits for the coefficients.
    Returns: list
        A list containing three points in the line drawn by the 2 original points.
    """
    # print("Making the line")
    # formar a linha
    diff = [(c1-c0)/2 for c0,c1 in zip(coefs[0],coefs[1])]
    new_points = [[c0+d for c0,d in zip(coefs[0],diff)], 
                  [c0-d for c0,d in zip(coefs[0],diff)],
                  [c1+d for c1,d in zip(coefs[1],diff)]]
    # for lst in new_points: print(['%.3f'%val for val in lst])
    new_points = [fix_coef(coef, upper_limits, lower_limits) for coef in new_points]
    # for lst in new_points: print(['%.3f'%val for val in lst])

    return new_points

def multi_objective_optimization(normal_data, indicators, thresholds=None, coef=None,
                            mu_x=weighted_arithimetic_mean, out_max=None, out_min=None, ans_max=None, ans_min=None,
                            limit_mquality = 0.001, limit_mdiff = 0.001, limit_mstep=200,
                            dstep = 0.01, limit_dquality = 0.0001, limit_nquality = 0.0001, limit_nstep=10000,
                            upper_limits = None, lower_limits = None, importance_factors=None,
                            multi_objective_chooser=MultiObjective):
    """
    Performs multi-objective optimization on the given normalized data using specified indicators and thresholds.
    Parameters:
    normal_data : DataFrame
        A pandas DataFrame containing the normalized data for the optimization.
    indicators : list
        A list of indicator functions to be used in the optimization.
    thresholds : list, optional
        A list of thresholds for the multi-criteria optimization. If None, defaults to [1 for _ in indicators].
    coef : list, optional
        Initial coefficients for the optimization. If None, equal weights are used.
    mu_x : function, optional
        Aggregate function that combines each line of the data with the supposed answer. Default is normal_weighted_arithimetic_mean.
    out_max : list, optional
        List to store the maximum values of the indicators.
    out_min : list, optional
        List to store the minimum values of the indicators.
    limit_mquality : float, optional
        Limit for the difference between the best coefficients on the multi-criteria optimization. Default is 0.001.
    limit_mdiff : float, optional
        Limit for the difference between the best coefficients on the multi-criteria optimization. Default is 0.01.
    limit_mstep : int, optional
        Maximum number of steps for the multi-criteria optimization. Default is 20.
    dstep : float, optional
        Step size for the optimization process. Default is 0.01.
    limit_dquality : float, optional
        Limit for the quality of the distribution in the mono-objective optimization. Default is 0.0001.
    limit_nquality : float, optional
        Limit for the quality of the distribution in the mono-objective optimization. Default is 0.0001.
    limit_nstep : int, optional
        Maximum number of steps for the mono-objective optimization. Default is 5000.
    upper_limits : list, optional
        Upper limits for the coefficients.
    lower_limits : list, optional
        Lower limits for the coefficients.
    multi_objective_chooser : function, optional
        Function to choose the best coefficients based on the multi-criteria optimization.
    Returns: list
        A list of optimized coefficients based on the multi-criteria optimization.
    Parametric returns:
    out_max : list
        List containing the maximum values of the indicators after optimization.
    out_min : list
        List containing the minimum values of the indicators after optimization.
    """
    # print(importance_factors)
    if coef is None:
        coef = [1/normal_data.shape[1] for _ in range(normal_data.shape[1])]
    if thresholds is None:
        thresholds = [1 for _ in indicators]
    if upper_limits is None:
        upper_limits = [1 for _ in range(normal_data.shape[1])]
    if lower_limits is None:
        lower_limits = [0 for _ in range(normal_data.shape[1])]
    # print(importance_factors)
    
    coef = fix_coef(coef, upper_limits, lower_limits)
    # print(importance_factors)
    normal_indicators, best_coefs = find_normal_indicators(
        normal_data, indicators,
        mu_x, dstep, coef,
        limit_dquality, limit_nstep,
        upper_limits, lower_limits,
        importance_factors,
        out_min, out_max,
        ans_min, ans_max
    )
    chooser = multi_objective_chooser(normal_indicators, thresholds=thresholds)
    best_coefs = optimize_best_2(
        best_coefs, normal_data,
        limit_mdiff, mu_x, dstep,
        limit_nquality, limit_nstep,
        upper_limits, lower_limits,
        chooser
   )
    if len(best_coefs) == 1:
        return best_coefs[0]
    
    for k in range(limit_mstep):
        # print("Calculating {}'th multiobjective optimization".format(k))

        
        #Making the line
        new_points = making_the_line(best_coefs, upper_limits, lower_limits)
        # Escolher melhor ponto
        cis = [normal_data.apply(lambda row: mu_x(coef, row), axis=1) for coef in new_points]
        point_qualities = [(i, chooser(ci)) for i, ci in enumerate(cis)]
        point_qualities.sort(key=lambda x: x[1], reverse=True)
        print(point_qualities)
        # otimizar melhor ponto.
        # print("Optimizing best point")
        best_coefs.append(optimization(
            normal_data, chooser,
            coef=new_points[point_qualities[0][0]], mu_x=mu_x, dstep=dstep,
            limit_dquality=limit_nquality, limit_nstep=limit_nstep,
            upper_limits=upper_limits, lower_limits=lower_limits
        ))
        # for lst in best_coefs: print(['%.3f'%val for val in lst])
            
        # Volta a escolher entre os 3 melhores
        # print("Calculating normal qualities")
        cis = [normal_data.apply(lambda row: mu_x(coef, row), axis=1) for coef in best_coefs]
        best_qualities = [(i, chooser(ci)) for i, ci in enumerate(cis)]
        best_qualities.sort(key=lambda x: x[1], reverse=True)
        best_coefs = [
            best_coefs[quality[0]] for quality in best_qualities[:2]
        ]
        # display(best_qualities)
        if best_qualities[2][0] == 2:
            print("Found best quality")
            print(best_qualities[0][1])
            break
        if all((abs(best_qualities[i][1]-q[1])<limit_mquality for i in range(len(best_qualities)) for q in best_qualities[i+1:])):
            print("No better quality found")
            print(best_qualities[0][1])
            break
        if all((abs(c1-c0)<limit_mdiff for c0,c1 in zip(best_coefs[0],best_coefs[1]))):
            print("No more different points")
            print(best_qualities[0][1])
            break
        # for lst in best_coefs: print(['%.3f'%val for val in lst])
    return best_coefs[0]
