def add_library_constraints(
    model,
    data,
    variables
):
    """
    Library is a filler activity.

    We do not create a CP-SAT class variable for Library.
    After all mandatory classes are scheduled, unused
    periods are converted to Library in the output.

    Therefore Library does not consume:
        - faculty
        - lab
        - batch resources
    """

    return