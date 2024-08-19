import pandas as pd

# raw data (from web scraping) csv column headings
return_df = pd.DataFrame(columns=['idx', 'country', 'region', 'city', 'store', 'name', 'brand', 'aisle',
                                  'subaisle', 'subsubaisle', 'size', 'price', 'multi_price', 'old_price', 'pricePerUnit',
                                  'itemNum', 'description', 'serving', 'img_urls', 'item_label',
                                  'item_ingredients', 'deliveryCo', 'url', 'timeStamp'])

# cleaned data csv column headings
clean_dat = pd.DataFrame(columns=[
                                # idx
                                  "ID",
                                # location pdf
                                  "Country",
                                  "Store",
                                  "DeliveryCo",
                                  "Region",
                                  "City",
                                # aisle
                                  "ProductAisle",
                                  "ProductAisle_DV",
                                # sub category
                                  "ProductCategory",
                                # sub sub category
                                  "ProductSubCategory",
                                  "ProductSubCategory_DV",
                                # img_urls
                                  "ProductImages",
                                # brand
                                  "ProductBrand",
                                # name
                                  "ProductName",
                                # from name
                                # from description
                                  "ProductVariety",
                                  "ProductFlavour",
                                # from pack
                                  "Packsize_org",
                                # from portion
                                  "Unitpp",
                                # from size
                                  "Containersize_org",
                                # from size
                                  "Containersize_val",
                                # from size
                                  "Containersize_unit",
                                # from description or null
                                  "Pack_type",
                                # CHECK
                                  "Netcontent_org",
                                  "Netcontent_val",
                                  "Netcontent_unit",
                                # CHECK
                                  "Description",
                                # description
                                  "Ingredients",
                                # ADDITIONAL
                                  "NutrInfo_org",
                                # serving
                                  "Servsize_container_type_org",
                                  "Servsize_container_type_val",
                                  "Servsize_container_type_unit",
                                # serving
                                  "Servsize_portion_org",
                                  "Servsize_portion_val",
                                  "Servsize_portion_unit",
                                  "Servings_cont",
                                # nutr label
                                  "Nutr_label",
                                # from nutrition label
                                  "Cals_org_pp",
                                  "Cals_value_pp",
                                  "Cals_unit_pp",
                                # group
                                  "TotalCarb_g_pp",
                                  "TotalCarb_pct_pp",
                                # group
                                  "TotalSugars_g_pp",
                                  "TotalSugars_pct_pp",
                                # group
                                  "AddedSugars_g_pp",
                                  "AddedSugars_pct_pp",
                                # group
                                  "Cals_value_p100g",
                                  "Cals_unit_p100g",
                                # group
                                  "TotalCarb_g_p100g",
                                  "TotalCarb_pct_p100g",
                                # group
                                  "TotalSugars_g_p100g",
                                  "TotalSugars_pct_p100g",
                                # group
                                  "AddedSugars_g_p100g",
                                  "AddedSugars_pct_p100g",
                                # something
                                  "ProdType",
                                  "StorType",
                                  "ItemNum",
                                  "SKU",
                                  "UPC",
                                  "URL",
                                  "DataCaptureTimeStamp",
                                  "Notes",])
