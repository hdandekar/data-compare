class Helper():

    def strip(x):
        """[summary]
        Arguments:
            x {[type]} -- [strip out whitespaces]
        Returns:
            [type] -- [description]
        """
        return x.strip() if isinstance(x, str) else x
        # print("From Utils.strip m print the value of x:{}".format(x))
