import pandas as pd
from ebaysdk.finding import Connection as finding

def check_current_listings(brand,model):
    df_realtime = pd.DataFrame(columns=['modelId','brand','model','title', 'price', 'listingType'])
    cam_catalog = pd.read_csv('./webapp/static/data/camera_catalog.csv')
    cam_catalog.fillna('',inplace =True)
    selected_model = cam_catalog[(cam_catalog['brand']==brand.lower())&(cam_catalog['model']==model)].iloc[0]
    modelId = selected_model['modelId']
    brand = selected_model['brand']
    model = selected_model['model']
    model_variants = selected_model['search'].replace('|',',')
    minus = selected_model['minus']
    keywords = brand + ' (' + model_variants + ') ' + minus + ' -parts -repair -read'

    api = finding(config_file='./webapp/static/ebayapi_key.yaml')

    api_request = {
        'keywords': keywords,
        'categoryId': 31388, # digital cameras = 31388
        'itemFilter': [{'name': 'Condition', 'value': 'Used'},
            {'name': 'LocatedIn', 'value': 'US'}],
        }
    response = api.execute('findItemsAdvanced', api_request)
    num_pages = int(response.reply.paginationOutput.totalPages)

    for page_number in range(1,num_pages+1):
        api_request = {
            'keywords': keywords,
            'categoryId': 31388, # digital cameras = 31388
            'itemFilter': [{'name': 'Condition', 'value': 'Used'},
                {'name': 'LocatedIn', 'value': 'US'}],
                'paginationInput': {'pageNumber': page_number},
            'outputSelector': ['SellerInfo']
            }
        response = api.execute('findItemsAdvanced', api_request)
        items = response.reply.searchResult.item
        for item in items:
            # select true "Used" cameras (instead of refurbished or for parts listings)
            # conditionId for used cameras is '3000'
            if item.condition.conditionId != '3000':
                continue
            # not interested in store data
            if item.listingInfo.listingType == 'StoreInventory':
                continue
            if int(item.sellerInfo.feedbackScore) > 10000:
                continue

            title = item.title.lower()
            price = float(item.sellingStatus.currentPrice.value)
            listingType = item.listingInfo.listingType.lower()
            listing = [modelId,brand,model,title,price,listingType]
            df_realtime.loc[len(df_realtime),:] = listing
            
    df_realtime = df_realtime[df_realtime['title'].apply(filter_dslr)]
    
    return df_realtime


# get rid of listings that are not functional or "body only"
def filter_dslr(title):
    if 'body only' in title:
        return True
    if any(word in title for word in (
        'as is','as-is','mm ','lenses'
        '24-105','24-70','28-135','28-80','28-75','17-85','18-55',
        '18-135','70-200','70-300','75-300','55-200','55-250','15-45')):
        return False
    if 'lens' in title and 'no lens' not in title:
        return False        
    return True

