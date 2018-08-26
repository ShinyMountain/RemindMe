

class Helper:

    @staticmethod
    def getElement(dictionary, key, optional=False):
        if key in dictionary.keys():
            return dictionary[key]
        if optional:
            return None

        raise Exception("Key " + key + " does not exists in the dictionary")
