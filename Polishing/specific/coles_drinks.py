from specific.coles import Coles
INDEX = 53;
COUNTRY = "Australia"

class ColesDrinks(Coles):
    @staticmethod
    def indices(index, dirty, clean):
        global INDEX
        try:
            clean.loc[index, 'ID'] = INDEX
        except Exception as e:
            None

    @staticmethod
    def country(index, clean):
        global COUNTRY
        try:
            clean.loc[index, 'Country'] = COUNTRY
        except Exception as e:
            None
    
    @staticmethod
    def region(index, clean):
        try:
            clean.loc[index, 'Region'] = 'Western Australia'
        except Exception as e:
            None

    @staticmethod
    def city(index, clean):
        try:
            clean.loc[index, 'City'] = 'North Perth'
        except Exception as e:
            None

    @staticmethod
    def store(index, clean):
        try:
            clean.loc[index, 'Store'] = 'Coles'
        except Exception as e:
            None


