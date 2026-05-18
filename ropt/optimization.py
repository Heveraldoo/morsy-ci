def Pertinence(index):
    """
    Returns the evaluation function of the aggregation function at object in index.
    Parameters:
    index : int
        The index of the object to be evaluated.
    Returns: function
        The evaluation function of the aggregation function at object in index.
    """
    def Evaluation(ci):
        return ci[index]
    return Evaluation

def PertinenceMin(index):
    """
    Returns the evaluation function of the aggregation function at object in index for minimization.
    Parameters:
    index : int
        The index of the object to be evaluated.
    Returns: function
        The evaluation function of the aggregation function at object in index for minimization.
    """
    def Evaluation(ci):
        return -ci[index]
    return Evaluation

def MultiObjective(indicators, thresholds=None):
    """
    Returns the evaluation function of the multi-objective optimization based on the provided indicators and thresholds.
    Parameters:
    indicators : list of functions
        A list of functions representing the objective to be evaluated.
    thresholds : list of floats, optional
        A list of thresholds for each indicator. If not provided, defaults to a list of ones.
    Returns: function
        The evaluation function that applies the objective and thresholds to a given input.
    """
    if thresholds is None:
        thresholds = [1 for _ in indicators]

    def Evaluation(ci):
        tmp = [indicator(ci) for indicator in indicators]
        qualities = [indicator for indicator,threshold in zip(tmp, thresholds) if indicator < threshold]
        if len(qualities) == 0:
            qualities = list(tmp)
        return min(qualities)
    return Evaluation
    
def MultiObjectiveSum(indicators, thresholds=None):
    """
    Returns the evaluation function of the multi-objective optimization based on the provided objective and thresholds.
    This function sums the values of the objective that are below their respective thresholds.
    Parameters:
    indicators : list of functions
        A list of functions representing the objective to be evaluated.
    thresholds : list of floats, optional
        A list of thresholds for each indicator. If not provided, defaults to a list of ones.
    Returns: function
        The evaluation function that applies the objective and thresholds to a given input.
    """
    if thresholds is None:
        thresholds = [1 for _ in indicators]

    def Evaluation(ci):
        tmp = [indicator(ci) for indicator in indicators]
        qualities = [indicator for indicator,threshold in zip(tmp, thresholds) if indicator < threshold]
        if len(qualities) == 0:
            qualities = list(tmp)

        return sum(qualities)
    return Evaluation

def FctMultiObjectiveRoot(p=2):
    """
    Returns the evaluation function of the multi-objective optimization based on the provided objective and thresholds.
    This function applies a root transformation to the sum of the objective.
    Parameters:
    p : int, optional
        The root degree to be applied to the sum of the objective. Default is 2 (standard vector length).
    Returns: function
        The factory of the evaluation function that applies the objective and thresholds to a given input.
    
    For example, after calling multi_indicator = FctMultiObjectiveRoot(3), the returned function will need to be called again as objective = multi_indicator(indicators) to create the actual evaluation function.
    """
    def Objective(indicators, thresholds=None):
        if thresholds is None:
            thresholds = [1 for _ in indicators]
    
        def Evaluation(ci):
            tmp = [indicator(ci) for indicator in indicators]
            qualities = [indicator**p for indicator,threshold in zip(tmp, thresholds) if indicator < threshold]
            if len(qualities) == 0:
                qualities = list(tmp)
    
            return sum(qualities) ** (1/p)
        return Evaluation
    return Objective

def NormalizeIndicator(indicator, ma, mi):
    """
    Returns the evaluation function of the objective normalized to a range defined by maximum and minimum values.
    Parameters:
    indicator : function 
        The evaluator of the objective function to be normalized.
    ma : float
        The maximum value for normalization.
    mi : float
        The minimum value for normalization.
    Returns: function
        The evaluation function of the objective.
    """
    def Evaluation(ci):
        return (indicator(ci)-mi)/(ma-mi)
    if ma==mi:
        def Evaluation(ci):
            return 1
    return Evaluation

def ImportanceIndicator(indicator, importance):
    """
    Returns the evaluation function of the objective that applies an importance factor to the indicator.
    Parameters:
    indicator : function
        The evaluator of the objective function to be weighted.
    importance : float
        The importance factor to be applied to the indicator.
    Returns: function
        The evaluation function of the objective with the applied factors.
    """
    def Evaluation(ci):
        return indicator(ci) ** importance
    return Evaluation