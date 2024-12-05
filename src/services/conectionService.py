from requests import get, post
from json import loads, dumps
from base64 import b64encode

class ConectionService:

  def getNext(self, config):
    user = b64encode(config['user'].encode("ascii"))
    Headers = { 
      "Content-Type" : "application/json",
      "X-USER-TOKEN" : user
    }
    endpoint = config['api'] + "/rules?pos=" + config['pos']
    jsonResponse = get(endpoint, headers = Headers)
    response = loads(jsonResponse.text)
    return response
  
  def logSong(self, song, config):
    user = b64encode(config['user'].encode("ascii"))
    fromObject = {
      "title": song['song']['title'],
      "author": song['song']['artist'],
      "song_id": int(song['song']['id']),
      "point_of_sale": int(config['pos']),
      "rule_id": int(song['ruleId']),
      "name_rule": song['name']
    }
    endpoint = config['api'] + "/rules";
    
    Headers = { 
      "Content-Type" : "application/json",
      "X-USER-TOKEN" : user
    }
    jsonResponse = post(endpoint, data=dumps(fromObject), headers = Headers)
    response = loads(jsonResponse.text)
    return response
  
  def songByRule(self, id, config):
    user = b64encode(config['user'].encode("ascii"))
    endpoint = config['cms'] + "/player/song/" + id;
    
    Headers = { 
      "Content-Type" : "application/json",
      "X-USER-TOKEN" : user
    }
    jsonResponse = get(endpoint, headers = Headers)
    response = loads(jsonResponse.text)
    return response