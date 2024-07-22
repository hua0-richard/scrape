import pandas as pd


class mappings:
    @staticmethod
    def preprocess(clean):
        try:
            return pd.DataFrame()
        except Exception as e:
            None
    @staticmethod
    def indices(index, dirty, clean):
        try:
            clean.loc[index, 'ID'] = dirty.loc[index, 'idx']
        except Exception as e:
            None
    
    # country, region, city, store
    @staticmethod
    def country(index, clean):
        try:
            None
        except Exception as e:
            None
    
    @staticmethod
    def region(index, clean):
        try:
            None
        except Exception as e:
            None

    @staticmethod
    def city(index, clean):
        try:
            None
        except Exception as e:
            None

    @staticmethod
    def store(index, clean):
        try:
            None
        except Exception as e:
            None

    @staticmethod
    def name(index, dirty, clean):
        try:
            clean.loc[index, 'ProductName'] = dirty.loc[index, 'name']
        except Exception as e:
            None

    @staticmethod
    def brand(index, dirty, clean):
        try:
            clean.loc[index, 'ProductBrand'] = dirty.loc[index, 'brand']
        except Exception as e:
            None

    @staticmethod
    def aisle(index, dirty, clean):
        try:
            aisle = ''
            if (dirty.loc[index, 'aisle']):
                aisle = dirty.loc[index, 'aisle']
            clean.loc[index, 'ProductAisle'] = aisle

        except Exception as e:
            None

    @staticmethod
    def subaisle(index, dirty, clean):
        try:
            subaisle = ''
            if (dirty.loc[index, 'subaisle']):
                subaisle = dirty.loc[index, 'subaisle']
            clean.loc[index, 'ProductCategory'] = subaisle
        except Exception as e:
            None
    
    @staticmethod
    def subsubaisle(index, dirty, clean):
        try:
            subsubaisle = ''
            if (dirty.loc[index, 'subsubaisle']):
                subsubaisle = dirty.loc[index, 'subsubaisle']
            clean.loc[index, 'ProductSubCategory'] = subsubaisle

        except Exception as e:
            None

    @staticmethod
    def size(index, dirty, clean):
        try:
            clean.loc[index, 'Packsize_org'] = dirty.loc[index, 'size']
        except Exception as e:
            None

    def containersize_org(index, dirty, clean):
        try:
            None
        except:
            None

    @staticmethod
    def servsize_portion_org(index, dirty, clean):
        try:
            None
        except:
            None

    @staticmethod
    def servings_cont(index, dirty, clean):
        try:
            None
        except:
            None
    @staticmethod
    def servsize_portion_org(index, dirty, clean):
        try:
            None
        except:
            None

    @staticmethod
    def price(index, dirty, clean):
        try:
            clean.loc[index, 'Price'] = dirty.loc[index, 'price']
        except Exception as e:
            None

    @staticmethod
    def multi_price(index, dirty, clean, dirty_key, clean_key):
        try:
            clean.loc[index, clean_key] = dirty.loc[index, dirty_key]
        except Exception as e:
            None

    @staticmethod
    def old_price(index, dirty, clean, dirty_key, clean_key):
        try:
            clean.loc[index, clean_key] = dirty.loc[index, dirty_key]
        except Exception as e:
            None

    @staticmethod
    def price_per_unit(index, dirty, clean):
        try:
            clean.loc[index, 'Price_perunit_value'] = dirty.loc[index, 'pricePerUnit']
        except Exception as e:
            None

    @staticmethod
    def itemNum(index, dirty, clean):
        try:
            clean.loc[index, 'ItemNum'] = dirty.loc[index, 'itemNum']
        except Exception as e:
            None

    @staticmethod
    def description(index, dirty, clean):
        try:
            clean.loc[index, 'Description'] = dirty.loc[index, 'description']
        except Exception as e:
            None

    @staticmethod
    def serving(index, dirty, clean, dirty_key, clean_key):
        try:
            clean.loc[index, clean_key] = dirty.loc[index, dirty_key]
        except Exception as e:
            None

    @staticmethod
    def img_urls(index, dirty, clean):
        try:
            clean.loc[index, 'ProductImages'] = dirty.loc[index, 'img_urls']
        except Exception as e:
            None

    @staticmethod
    def item_label(index, dirty, clean):
        try:
            clean.loc[index, 'Nutr_label'] = dirty.loc[index, 'item_label']
        except Exception as e:
            None

    @staticmethod
    def item_ingredients(index, dirty, clean):
        try:
            clean.loc[index, 'Ingredients'] = dirty.loc[index, 'item_ingredients']
        except Exception as e:
            None

    @staticmethod
    def url(index, dirty, clean):
        try:
            clean.loc[index, 'URL'] = dirty.loc[index, 'url']
        except Exception as e:
            None

    @staticmethod
    def allergen_info(index, dirty, clean, dirty_key, clean_key):
        None

    @staticmethod
    def sku(index, dirty, clean):
        try:
            clean.loc[index, 'SKU'] = dirty.loc[index, 'SKU']
        except Exception as e:
            print(e)
        
    @staticmethod
    def time_stamp(index, dirty, clean):
        try:
            clean.loc[index, 'DataCaptureTimeStamp'] = dirty.loc[index, 'timeStamp']
        except Exception as e:
            None

