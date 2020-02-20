# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 12:01:12 2020

@author: Keinan Marks

"""




#Internal Libraries
import json
import requests
from datetime import date, timedelta, datetime
import os


#External Dependencies
import arcgis
from arcgis.gis import GIS
from arcgis import features
from arcgis.geocoding import Geocoder,batch_geocode
from arcgis.features import FeatureLayerCollection


#This is an overwrought function to geocode an array from a list of geocoding services.
#If you aren't using more than one geocoder, probably better to just use the built in batch_geocode or geocode_from_file
#But this should still work fine
#Defined as used in credentials.json


#Basically uses batch_geocode for a pass via the primary and the geocode function to fill in the gaps moving down the list.
#Some additional logic that was written specifically for city of los angeles bureau of engineering services, ie take match >85 with zip
#Take match >95 without zip
def collect_and_geocode_addresses_batch(array1,address_index,gis,geocoder_list = [],pass_nan = True,lat_index = False, sr = 4326):
    array = array1
    batches = int(len(array)/1000) + 2
    from arcgis.gis import GIS
    from arcgis.geocoding import get_geocoders, batch_geocode, Geocoder, geocode
    address_list = []
    inter_list = {}
    for address in array:
        address_list.append(address[address_index])
    geocoder = Geocoder(geocoder_list[0],gis=gis)
    try:
        del results
    except:
        pass
    for r in range(1,batches):
        #print(r)
        start = 1000 * (r - 1)
        end = 1000 * r

        try:
            results.extend(batch_geocode(address_list[start:end],geocoder = geocoder,out_sr = sr))
        except Exception as e:
            #print(e)
            results = batch_geocode(address_list[start:end],geocoder = geocoder,out_sr = sr)
        #print(results)
    for index,value in enumerate(results):
        try:
            inter_list[index]
            continue
        except:
            try:
                if [value['location']['x'],value['location']['y']] != ['NaN', 'NaN']:
                    inter_list[index] = [value['location']['x'],value['location']['y'],str(value['attributes']['Match_addr']).replace(',','')]
            except Exception as e:
                #print(e)
                pass
    
    if pass_nan == True:
        for i in range(0,len(address_list)):
            try:
                a = inter_list[i]
            except:
                for geocoders in geocoder_list[1:]:
                    if address_list[i] == 'NONE':
                        inter_list[i] = ['NaN', 'NaN','NaN']
                        break
                    try:
                        #print(geocoders,address_list[i])
                        geocoder = Geocoder(geocoders,gis = gis)
                        value = geocode(address_list[i], geocoder = geocoder,out_sr = sr)
                        if len(value) > 0:
                            if [value[0]['location']['x'],value[0]['location']['y']] != ['NaN', 'NaN'] and int(value[0]['score']) > 85:
                                inter_list[i] = [value[0]['location']['x'],value[0]['location']['y'],str(value[0]['attributes']['Match_addr']).replace(',','')]
                                #print(inter_list[i],geocoders)
                                break
                        try:

                            value = geocode((address_list[i].split(','))[0], geocoder = geocoder,out_sr = sr)
                            if len(value) > 0:

                                #if [value[0]['location']['x'],value[0]['location']['y']] != ['NaN', 'NaN'] and int(value[0]['score']) > 95:
                                if int(value[0]['score']) > 95:
                                    #print('matched without zip')
                                    inter_list[i] = [value[0]['location']['x'],value[0]['location']['y'],str(value[0]['attributes']['Match_addr']).replace(',','')]
                                    break
                                    #print(inter_list[i],geocoders)
                            else:                                    
                                inter_list[i] = ['NaN', 'NaN','NaN']
                        except Exception as e:
                            print(e,value,address_list[i].split(','))[0]
                            inter_list[i] = ['NaN', 'NaN','NaN']

                    except Exception as e:
                        #print(e,value)
                        inter_list[i] = ['NaN', 'NaN','NaN']
    else:
        pass
    for k,v in inter_list.items():
        try:
            array[k].append(v[1])
        except:
            array[k].append(v[1])
        try:
            array[k].append(v[0])
        except:
            array[k].append(v[0])


        
    return array


#returns the index of a value in a list in a list\array
def find_index_value(array,value,header_index = 0):
    for index,val in enumerate(array[header_index]):
        if val == value:
            return index
        
    return ''



#overwrites a feature layer with passed item_id (must have same schema as original service)
#If no item_id is passed, creates a new feature service named from the credentials file
def overwrite_feature_layer(csv_file,feature_layer_id,username,password,gis,updates=[],mappings = {}, parameters = {}):
    from arcgis.gis import GIS
    from arcgis import features
    from arcgis.features import FeatureLayerCollection
    from arcgis.gis import ContentManager
    import datetime
    
    #add csv to portal
    if feature_layer_id == '' or None:
        print('Creating New Feature Service')
        csv_item = gis.content.add({}, csv_file)

        #publish portal csv to feature layer with pass params
        csv_lyr = csv_item.publish(publish_parameters = parameters)
        #might consider writing item id to credentials?
        return 'New Service Created, item id ' + str(csv_lyr.id)
    else:
        print('Beginning Update Process')
        try:
            date = datetime.datetime.now()

            inspections_feature_layer = gis.content.get(feature_layer_id)
            inspections_flayer_collection = FeatureLayerCollection.fromitem(inspections_feature_layer)
            response_1 = inspections_flayer_collection.manager.overwrite(csv_file)
            #response = inspections_flayer_collection.manager.overwrite(csv_path)
            updates.append(str(response_1) + ' - ' + str(date))
            print(updates[-1])
            
        except Exception as e:
            print('Failed to update feature layer')
            print(e)
            pass
        return updates


#dump array to csv
def dump_to_csv(array, out_path = 'out.csv'):
    import csv
    with open(out_path, 'w+', newline='\n') as csvfile:
        listwriter = csv.writer(csvfile)
        listwriter.writerows(array)
    return out_path


#This is a super hacky, temporary way to format the top level of a json into an array
#Needs better handling
def json_to_array(json_data):
    data = json.loads(json_data.text)

    output_array = []

    headers = []
    for header,value in data[0].items():
        headers.append(header)
    output_array.append(headers)
#This could be handled much better
#Attempt to clean it up to point where numerics are resolved
#and it is still standard csv compliant
#Will rewrite to appropriately type and convert fields at some point
    for vals in data:
        row = []
        for k,v in vals.items():
            try:
                row.append(float(v))
            except:
                #Wild encodings going on
                try:
                    row.append(str(v.encode('ascii','replace')).replace(',',' '))
                except:
                    #wild encodings
                    row.append(str(v).replace(',', ' '))
                    try:
                        row.append(','.join(v))
                    except:
                        row.append(' ')
        output_array.append(row)
    return output_array
        
#Body        
if __name__ == '__main__':
    
    then = datetime.today()
    then = then - timedelta(microseconds=then.microsecond)
    print("\nInitiating script at", then, "\n")
    
    
    #Collect all paramters from config json
    credentials_json = r"credentials.json"
    try:
        with open(credentials_json, 'r') as f:
            print("Loading Environment Variables...")
            credentials = json.load(f)
            #either arcgis online portal or hosted enterprise
            arcgis_portal = credentials['arcgis_portal']
            
            #agol or portal username. for domain use DOMAIN\\USERNAME eg SAN\\388560
            username = credentials['username']
            password = credentials['password']
            json_source = credentials['json_source']
            geocoder_list = credentials['geocoder_list']
            geocoding = credentials['geocoding']
            lat = credentials['latitude_field_name']
            lng = credentials['longitude_field_name']
            address = credentials['address_field_name']
            feature_layer_id = credentials['item_id']
            new_service_name = credentials['new_service_name']
            proxy_bypass = credentials['proxy_bypass']
            
            
            #This helps resolve hitting internal arcgis enterprise servers behind a proxy
            if proxy_bypass != '':
                os.environ['NO_PROXY'] = proxy_bypass
            
            response = requests.get(json_source)
            
    except:
        print('Missing Values in Credentials json')
        
        
        
    array = json_to_array(response)   
    #Create GIS object from defined portal, username and password
    gis = GIS(arcgis_portal,username,password)
    
    #Add lat and long to each array row is geocoding flag != no
    if geocoding.upper() != 'NO':
        #get the index of the address to pass to the geocoder
        address_index = find_index_value(array,address)
        array = collect_and_geocode_addresses_batch(array,address_index,gis)
        #change passed lat long headers to those assigned by the bonkers function
        lat = 'Latitude'
        lng = 'Longitude'
    
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    
    #Assumed xy
    #publish params docs available here: https://developers.arcgis.com/rest/users-groups-and-items/publish-item.htm
    params = {'locationType' : 'coordinates', 'latitudeFieldName' : lat, 'longitudeFieldName' : lng}
    
    #output csv to script directory
    csv_object = dump_to_csv(array, out_path = new_service_name + '.csv')
    #push csv to portal
    overwrite_feature_layer(csv_object,feature_layer_id,username,password,gis,mappings = mapping, parameters = params)
    sys.exit('Complete')
