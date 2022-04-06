# !pip install bcrypt
# !pip install chacha20poly1305

import os
import time
import bcrypt
from chacha20poly1305 import ChaCha20Poly1305
from datetime import date

class ConstantClass:
  def __init__(self,nSubkeys=18):
    self.KEY = b'\x81\x05\xee\xa6a\xb4\xd0?\xaf\xf7\x05\x89V\x8d=K\xd45\xf1o\xacI<L\x94\x9f\x10\xa9\x11\xedU\x83'  #os.urandom(32)
    self.NONCE = b'th\xd5\xc5>\n\x88\x8ed\xbf\xf3\xf5'  # os.urandom(12)
    self.noOfSubkeys = nSubkeys

  def saltGeneration(self):
    salt = bcrypt.gensalt()
    saltedString = str(salt)
    return  salt, saltedString

  def keyGenerationOfSalt(self,KEY,NONCE,salt,requiredLength):
    cip = ChaCha20Poly1305(KEY)
    if type(salt) == type("uncertain"):
      salt =  bytes(salt, 'utf-8')
    ciphertext = cip.encrypt(NONCE, salt)
    saltEncryptionKey =  ''.join(format(i, '08b') for i in ciphertext)
    if len(saltEncryptionKey) >= requiredLength :
      return saltEncryptionKey[:requiredLength]
    currentlength = len(saltEncryptionKey)  
    noOfAppend = requiredLength // currentlength  
    return str(saltEncryptionKey + saltEncryptionKey*noOfAppend)[:requiredLength]

  def xor(self,a,b):
    if len(a)==len(b):
      ans = ''
      for i,j in zip(a,b):
        ans += str(int(i)^int(j))
      return ans
    else:
      print(f'Length are not same as {len(a)} != {len(b)}')

  def binaryStringToAscii(self,binaryString):
    asciiString =''
    for i in range(0, len(binaryString), 8):
      tempData = binaryString[i:i + 8]
      decimalData =  int(tempData, 2)
      asciiString = asciiString + chr(decimalData)
    return asciiString

  def asciiTobinaryString(self,asciiString):
    # Converting String to binary
    binaryString =  ''.join(format(i, '08b') for i in bytearray(asciiString, encoding ='utf-8'))
    return binaryString

  def add2BinaryString(self,x,y):
      max_len = max(len(x), len(y))
      x = x.zfill(max_len)
      y = y.zfill(max_len)
      # initialize the result
      result = ''
      # initialize the carry
      carry = 0
      # Traverse the string
      for i in range(max_len - 1, -1, -1):
        r = carry
        r += 1 if x[i] == '1' else 0
        r += 1 if y[i] == '1' else 0
        result = ('1' if r % 2 == 1 else '0') + result
        carry = 0 if r < 2 else 1  # Compute the carry.
      
      if carry !=0 : result = '1' + result
      resultFinal = result.zfill(max_len)
      modifiedResult = resultFinal[abs(len(resultFinal)-max_len):] 
      return resultFinal, modifiedResult 






class AdaptableHash(ConstantClass):
  def __init__(self,nSubkeys=18,subkeySize=32,constantSalt = b"Uncertainity",NumberOfRounds = 16,round_pumped = 10):
    super().__init__(nSubkeys)
    self.state = [] # List of Binary string Which are keys containg 18 sub-keys
    self.subkeySize = subkeySize
    self.constantSalt = constantSalt
    self.NumberOfRounds = NumberOfRounds
    self.round_pumped = round_pumped 
    self.initialSubKeys = self.keyGenerationOfSalt(self.KEY, self.NONCE, constantSalt, subkeySize * 18  )

  def compareHash(self,newPassword, originalHash):
    ''' Compare the stored hash in db with the hash generated by entering the  password by the user, note the salt is stored in encrypted form so it
    must be decrypted first before using it.Takes the input originalHash and newly entered passsword by the user. This method will be called after we have query the database and retreived the hashed password , requiredLength & encryptedSalt against the corresponding username.''' 
    saltedString = originalHash.decode('utf-8')
    val  = saltedString.find(".")
    saltedString = saltedString[6:val+1]
    HASH, encryptedSALT = self.HashingPhase(self.round_pumped,saltedString,newPassword)
    password = bytes(newPassword,encoding='utf-8')
    return self.alternateCheck(password,originalHash,saltedString)


  def GenerateHashANDSalt(self,password):
    '''
    This method is used to stored tehe first login password by user in form of hashed in database i.e. This method is called during the case when user
    first register to the side/ or that is for new user login.
    '''
    salt, saltedString = self.saltGeneration() 
    passwordHash, Encryptedsalt = self.HashingPhase(self.round_pumped ,saltedString,password)
    password = bytes(password,encoding='utf-8')
    h,s = self.alternate(password)
    return passwordHash, Encryptedsalt,h,s 


  def keyGenerationAndSetupPhase(self,round_pumped,salt,password):
    self.doInitialSetup()  # state <--- doInitialSetup()
    self.changeKeyConfiguration(self.state,salt,password)  #  state <--- changeKeyConfiguration(state,salt,key)
    for ith_round in range(2**round_pumped):
      state = self.changeKeyConfiguration(self.state,"0",salt)
      state = self.changeKeyConfiguration(self.state,"0",password)
    return 

  def HashingPhase(self,round_pumped,salt,password):
    state  = self.keyGenerationAndSetupPhase(round_pumped,salt,password) # AIM IS TO MAKE THIS STEP SLOWER
    print('KeyConfigurationSetup Done')
    cipherText = "Everything is Uncertain in this World"
    for i in range(64):
        cipherText  = self.getHash(state,cipherText)
    print('HASH IS OBTAINED Done')
    HASH, encryptedSALT = self.ConcatenatedHashValue(round_pumped,salt,cipherText,password)
    return HASH, encryptedSALT

  def doInitialSetup(self):
    self.state = []
    for i in range(0,self.subkeySize*18,self.subkeySize):
      self.state.append(self.initialSubKeys[i:i+32])

  def changeKeyConfiguration(self,state,salt,key):
    binaryKey = self.asciiTobinaryString(str(key))
    lengthOfBinaryKey = len(binaryKey)
    noOfAppend = (self.subkeySize*18)//lengthOfBinaryKey
    modifiedBinaryKey = binaryKey + binaryKey*noOfAppend if noOfAppend>0 else  binaryKey[:self.subkeySize*18]
    for i,j in zip(range(0,self.subkeySize*18, self.subkeySize ),range(0,18)):
      self.state[j] = self.xor(state[j],modifiedBinaryKey[i:i+self.subkeySize])
    if type(salt) != type("uncertain"):
      salt = str(salt)
    binarySalt = self.asciiTobinaryString(str(salt))  # This salt will be of 256 bits
    if len(binarySalt) != 2*128:
      if len(binarySalt) < 256 :
        noOfConcatenation = 256//len(binarySalt)
        binarySalt = str(binarySalt + binarySalt*noOfConcatenation)[:256]
      else:
        binarySalt = binarySalt[:256]

    actualBinarySalt =  self.xor(binarySalt[:128], binarySalt[128:]) # This salt will be of 128 bits
    for i in range(0,18//2):
      if i%2==0:
        tempCipher = self.getHash(state,actualBinarySalt[:64])
        self.state[2*i] = tempCipher[:32]
        self.state[2*i+1]=tempCipher[32:]
        actualBinarySalt = actualBinarySalt[:64] +  self.xor(actualBinarySalt[64:], tempCipher)
      else:
        tempCipher = self.getHash(state,actualBinarySalt[64:])
        self.state[2*i] = tempCipher[:32]
        self.state[2*i+1]=tempCipher[32:]
        actualBinarySalt = self.xor(actualBinarySalt[:64], tempCipher) + actualBinarySalt[64:]
    return


  def getHash(self,state,plainText):
    if type(plainText) == type("Uncertain"):
      plainText = self.asciiTobinaryString(plainText)
      # print("Length of plainText BEFORE", len(plainText))
      if len(plainText)%64 !=0:
        res = len(plainText)%64
        required = 64-res
        plainText = plainText + "0"*required
        print("Length of plainText", len(plainText))
         
    leftPlainText = ''
    rightPLainText = ''
    resultedHash = '0'*64
    for i in range(len(plainText),64):
      leftPlainText = plainText[i:i+32]
      rightPLainText = plainText[i+32:i+32+32]
      for roundNo in range(self.NumberOfRounds-1):
        #Loops for Total Rounds -1
        leftPlainText = self.xor(state[roundNo],leftPlainText)
        confusionDiffusionStream = self.confusionDiffusionBlock(leftPlainText)
        rightPLainText = self.xor(rightPLainText,confusionDiffusionStream)
        #swapping
        temp  = leftPlainText 
        leftPlainText = rightPLainText
        rightPLainText = temp
      #Last Round OPerations
      leftPlainText = self.xor(leftPlainText,state[-3])
      confusionDiffusionStream = self.confusionDiffusionBlock(leftPlainText)
      rightPLainText = self.xor(rightPLainText, confusionDiffusionStream)
      rightPLainText = self.xor(rightPLainText,state[-1])
      leftPlainText = self.xor(leftPlainText,state[-2])
      combinedText = leftPlainText + rightPLainText
      resultedHash = self.xor(resultedHash, combinedText)
    return resultedHash


  def confusionDiffusionBlock(self,binarystream):
    leftstream = binarystream[:len(binarystream)//2]
    rightstream = binarystream[len(binarystream)//2:]
    _ , addedStream = self.add2BinaryString(leftstream,rightstream)
    xorredstream = self.xor(leftstream, rightstream)
    resultstream = addedStream + xorredstream
    return resultstream 

  # def EncryptSalt(self,salt,password):
  #   '''
  #   In databse along with password hash we are also storing encrypted salt and its required_length=256 means 256 bits value of salt bt in ral actual salt is formed by
  #   takinh xor of left 128 bits with right 128 bits. 
  #   '''
  #   if type(salt) != type("uncertain") :# i.e class 'str'
  #     salt = str(salt)
  #   requiredLength = len(self.asciiTobinaryString(salt))
  #   # longEncryptionKey = self.keyGenerationOfSalt(self.KEY,self.NONCE,password,requiredLength)
  #   cipherText = self.xor(longEncryptionKey[:requiredLength], self.asciiTobinaryString(salt) )
  #   return cipherText,requiredLength

  # def decryptSalt(self,encryptedSALT,requiredLength,password):
  #   # longEncryptionKey = self.keyGenerationOfSalt(self.KEY,self.NONCE,password,requiredLength)
  #   salt = self.binaryStringToAscii( self.xor(encryptedSALT,longEncryptionKey) )
  #   return salt

  def detachCipherTextAndRoundPumpedFromHash(self,hashedString):
    subStr = "$$"
    occurrence = 2
    # Finding 2th occurrence of substring "$$"
    val = -1
    for i in range(0, occurrence):
        val = hashedString.find(subStr, val + 1)

    round_pumped = int(hashedString[2:val])
    cipherText = hashedString[val+2:]
    return round_pumped, cipherText
    
  def ConcatenatedHashValue(self,round_pumped,salt,cipherText,password):
    return f"$${round_pumped}$${cipherText}",(salt)

  def alternate(self, password):
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    return hashed,salt 

  def alternateCheck(self,password,hashed,saltedString=""):
    if bcrypt.checkpw(password, hashed):
      return True
    else:
      return False

  def compareHash_(self,newPassword, originalHash):
    password = bytes(newPassword,encoding='utf-8')
    return self.alternateCheck(password,originalHash)


  def GenerateHashANDSalt_(self,password):
    password = bytes(password,encoding='utf-8')
    h,s = self.alternate(password)
    return h,s 





def resultAndAnalysis(filename,colname):
  df = pd.read_csv(filename)
  result = {}
  for passwords in df[colname]:
    start = time.time()
    pwd = AdaptableHash()
    _,_h,s = pwd.GenerateHashANDSalt(passwords)
    # print(h)
    end = time.time()
    timeTaken = start - end 
    if len(passwords) in result.keys():
      result[len(passwords)] = [timeTaken, 1 , timeTaken/1]
    else:
      result[len(passwords)][0] += timeTaken
      result[len(passwords)][1] += 1
      result[len(passwords)][2] = result[len(passwords)][0]/result[len(passwords)][1]
  return result



 
if __name__ == "__main__":

  pwd = AdaptableHash()
  _, _,h,s = pwd.GenerateHashANDSalt("qwerty")
  print(h)
  password = "qwerty"
  print(pwd.compareHash(password, h))
  password = "qwerty1"
  print(pwd.compareHash(password, h))












































































































































































# # !pip install bcrypt
# # !pip install chacha20poly1305

# import os
# import time
# import bcrypt
# from chacha20poly1305 import ChaCha20Poly1305



# class ConstantClass:
#   def __init__(self,nSubkeys=18):
#     self.KEY = b'\x81\x05\xee\xa6a\xb4\xd0?\xaf\xf7\x05\x89V\x8d=K\xd45\xf1o\xacI<L\x94\x9f\x10\xa9\x11\xedU\x83'  #os.urandom(32)
#     self.NONCE = b'th\xd5\xc5>\n\x88\x8ed\xbf\xf3\xf5'  # os.urandom(12)
#     self.noOfSubkeys = nSubkeys

#   def saltGeneration(self):
#     salt = bcrypt.gensalt()
#     saltedString = str(salt)
#     return  salt, saltedString

#   def keyGenerationOfSalt(self,KEY,NONCE,salt,requiredLength):
#     cip = ChaCha20Poly1305(KEY)
#     if type(salt) == type("uncertain"):
#       salt =  bytes(salt, 'utf-8')
#     ciphertext = cip.encrypt(NONCE, salt)
#     saltEncryptionKey =  ''.join(format(i, '08b') for i in ciphertext)
#     if len(saltEncryptionKey) >= requiredLength :
#       return saltEncryptionKey[:requiredLength]
#     currentlength = len(saltEncryptionKey)  
#     noOfAppend = requiredLength // currentlength  
#     return str(saltEncryptionKey + saltEncryptionKey*noOfAppend)[:requiredLength]

#   def xor(self,a,b):
#     if len(a)==len(b):
#       ans = ''
#       for i,j in zip(a,b):
#         ans += str(int(i)^int(j))
#       return ans
#     else:
#       print(f'Length are not same as {len(a)} != {len(b)}')

#   def binaryStringToAscii(self,binaryString):
#     asciiString =''
#     for i in range(0, len(binaryString), 8):
#       tempData = binaryString[i:i + 8]
#       decimalData =  int(tempData, 2)
#       asciiString = asciiString + chr(decimalData)
#     return asciiString

#   def asciiTobinaryString(self,asciiString):
#     # Converting String to binary
#     binaryString =  ''.join(format(i, '08b') for i in bytearray(asciiString, encoding ='utf-8'))
#     return binaryString

#   def add2BinaryString(self,x,y):
#       max_len = max(len(x), len(y))
#       x = x.zfill(max_len)
#       y = y.zfill(max_len)
#       # initialize the result
#       result = ''
#       # initialize the carry
#       carry = 0
#       # Traverse the string
#       for i in range(max_len - 1, -1, -1):
#         r = carry
#         r += 1 if x[i] == '1' else 0
#         r += 1 if y[i] == '1' else 0
#         result = ('1' if r % 2 == 1 else '0') + result
#         carry = 0 if r < 2 else 1  # Compute the carry.
      
#       if carry !=0 : result = '1' + result
#       resultFinal = result.zfill(max_len)
#       modifiedResult = resultFinal[abs(len(resultFinal)-max_len):] 
#       return resultFinal, modifiedResult 
















# class AdaptableHash(ConstantClass):
#   def __init__(self,nSubkeys=18,subkeySize=32,constantSalt = b"Uncertainity",NumberOfRounds = 16,round_pumped = 10):
#     super().__init__(nSubkeys)
#     self.state = [] # List of Binary string Which are keys containg 18 sub-keys
#     self.subkeySize = subkeySize
#     self.constantSalt = constantSalt
#     self.NumberOfRounds = NumberOfRounds
#     self.round_pumped = round_pumped 
#     self.initialSubKeys = self.keyGenerationOfSalt(self.KEY, self.NONCE, constantSalt, subkeySize * 18  )

#   def compareHash(self,newPassword, originalHash):
#     ''' Compare the stored hash in db with the hash generated by entering the  password by the user, note the salt is stored in encrypted form so it
#     must be decrypted first before using it.Takes the input originalHash and newly entered passsword by the user. This method will be called after we have query the database and retreived the hashed password , requiredLength & encryptedSalt against the corresponding username.''' 
#     saltedString = originalHash.decode('utf-8')
#     val  = saltedString.find(".")
#     saltedString = saltedString[6:val+1]
#     HASH, encryptedSALT = self.HashingPhase(self.round_pumped,saltedString,newPassword)
#     password = bytes(newPassword,encoding='utf-8')
#     return self.alternateCheck(password,originalHash,saltedString)


#   def GenerateHashANDSalt(self,password):
#     '''
#     This method is used to stored tehe first login password by user in form of hashed in database i.e. This method is called during the case when user
#     first register to the side/ or that is for new user login.
#     '''
#     salt, saltedString = self.saltGeneration() 
#     passwordHash, Encryptedsalt = self.HashingPhase(self.round_pumped ,saltedString,password)
#     password = bytes(password,encoding='utf-8')
#     h,s = self.alternate(password)
#     return passwordHash, Encryptedsalt,h,s 


#   def keyGenerationAndSetupPhase(self,round_pumped,salt,password):
#     self.doInitialSetup()  # state <--- doInitialSetup()
#     self.changeKeyConfiguration(self.state,salt,password)  #  state <--- changeKeyConfiguration(state,salt,key)
#     for ith_round in range(2**round_pumped):
#       state = self.changeKeyConfiguration(self.state,"0",salt)
#       state = self.changeKeyConfiguration(self.state,"0",password)
#     return 

#   def HashingPhase(self,round_pumped,salt,password):
#     state  = self.keyGenerationAndSetupPhase(round_pumped,salt,password) # AIM IS TO MAKE THIS STEP SLOWER
#     print('KeyConfigurationSetup Done')
#     cipherText = "Everything is Uncertain in this World"
#     for i in range(64):
#         cipherText  = self.getHash(state,cipherText)
#     print('HASH IS OBTAINED Done')
#     HASH, encryptedSALT = self.ConcatenatedHashValue(round_pumped,salt,cipherText,password)
#     return HASH, encryptedSALT

#   def doInitialSetup(self):
#     self.state = []
#     for i in range(0,self.subkeySize*18,self.subkeySize):
#       self.state.append(self.initialSubKeys[i:i+32])

#   def changeKeyConfiguration(self,state,salt,key):
#     binaryKey = self.asciiTobinaryString(str(key))
#     lengthOfBinaryKey = len(binaryKey)
#     noOfAppend = (self.subkeySize*18)//lengthOfBinaryKey
#     modifiedBinaryKey = binaryKey + binaryKey*noOfAppend if noOfAppend>0 else  binaryKey[:self.subkeySize*18]
#     for i,j in zip(range(0,self.subkeySize*18, self.subkeySize ),range(0,18)):
#       self.state[j] = self.xor(state[j],modifiedBinaryKey[i:i+self.subkeySize])
#     if type(salt) != type("uncertain"):
#       salt = str(salt)
#     binarySalt = self.asciiTobinaryString(str(salt))  # This salt will be of 256 bits
#     if len(binarySalt) != 2*128:
#       if len(binarySalt) < 256 :
#         noOfConcatenation = 256//len(binarySalt)
#         binarySalt = str(binarySalt + binarySalt*noOfConcatenation)[:256]
#       else:
#         binarySalt = binarySalt[:256]

#     actualBinarySalt =  self.xor(binarySalt[:128], binarySalt[128:]) # This salt will be of 128 bits
#     for i in range(0,18//2):
#       if i%2==0:
#         tempCipher = self.getHash(state,actualBinarySalt[:64])
#         self.state[2*i] = tempCipher[:32]
#         self.state[2*i+1]=tempCipher[32:]
#         actualBinarySalt = actualBinarySalt[:64] +  self.xor(actualBinarySalt[64:], tempCipher)
#       else:
#         tempCipher = self.getHash(state,actualBinarySalt[64:])
#         self.state[2*i] = tempCipher[:32]
#         self.state[2*i+1]=tempCipher[32:]
#         actualBinarySalt = self.xor(actualBinarySalt[:64], tempCipher) + actualBinarySalt[64:]
#     return


#   def getHash(self,state,plainText):
#     if type(plainText) == type("Uncertain"):
#       plainText = self.asciiTobinaryString(plainText)
#       # print("Length of plainText BEFORE", len(plainText))
#       if len(plainText)%64 !=0:
#         res = len(plainText)%64
#         required = 64-res
#         plainText = plainText + "0"*required
#         print("Length of plainText", len(plainText))
         
#     leftPlainText = ''
#     rightPLainText = ''
#     resultedHash = '0'*64
#     for i in range(len(plainText),64):
#       leftPlainText = plainText[i:i+32]
#       rightPLainText = plainText[i+32:i+32+32]
#       for roundNo in range(self.NumberOfRounds-1):
#         #Loops for Total Rounds -1
#         leftPlainText = self.xor(state[roundNo],leftPlainText)
#         confusionDiffusionStream = self.confusionDiffusionBlock(leftPlainText)
#         rightPLainText = self.xor(rightPLainText,confusionDiffusionStream)
#         #swapping
#         temp  = leftPlainText 
#         leftPlainText = rightPLainText
#         rightPLainText = temp
#       #Last Round OPerations
#       leftPlainText = self.xor(leftPlainText,state[-3])
#       confusionDiffusionStream = self.confusionDiffusionBlock(leftPlainText)
#       rightPLainText = self.xor(rightPLainText, confusionDiffusionStream)
#       rightPLainText = self.xor(rightPLainText,state[-1])
#       leftPlainText = self.xor(leftPlainText,state[-2])
#       combinedText = leftPlainText + rightPLainText
#       resultedHash = self.xor(resultedHash, combinedText)
#     return resultedHash


#   def confusionDiffusionBlock(self,binarystream):
#     leftstream = binarystream[:len(binarystream)//2]
#     rightstream = binarystream[len(binarystream)//2:]
#     _ , addedStream = self.add2BinaryString(leftstream,rightstream)
#     xorredstream = self.xor(leftstream, rightstream)
#     resultstream = addedStream + xorredstream
#     return resultstream 

#   # def EncryptSalt(self,salt,password):
#   #   '''
#   #   In databse along with password hash we are also storing encrypted salt and its required_length=256 means 256 bits value of salt bt in ral actual salt is formed by
#   #   takinh xor of left 128 bits with right 128 bits. 
#   #   '''
#   #   if type(salt) != type("uncertain") :# i.e class 'str'
#   #     salt = str(salt)
#   #   requiredLength = len(self.asciiTobinaryString(salt))
#   #   # longEncryptionKey = self.keyGenerationOfSalt(self.KEY,self.NONCE,password,requiredLength)
#   #   cipherText = self.xor(longEncryptionKey[:requiredLength], self.asciiTobinaryString(salt) )
#   #   return cipherText,requiredLength

#   # def decryptSalt(self,encryptedSALT,requiredLength,password):
#   #   # longEncryptionKey = self.keyGenerationOfSalt(self.KEY,self.NONCE,password,requiredLength)
#   #   salt = self.binaryStringToAscii( self.xor(encryptedSALT,longEncryptionKey) )
#   #   return salt

#   def detachCipherTextAndRoundPumpedFromHash(self,hashedString):
#     subStr = "$$"
#     occurrence = 2
#     # Finding 2th occurrence of substring "$$"
#     val = -1
#     for i in range(0, occurrence):
#         val = hashedString.find(subStr, val + 1)

#     round_pumped = int(hashedString[2:val])
#     cipherText = hashedString[val+2:]
#     return round_pumped, cipherText
    
#   def ConcatenatedHashValue(self,round_pumped,salt,cipherText,password):
#     return f"$${round_pumped}$${cipherText}",(salt)

#   def alternate(self, password):
#     salt = bcrypt.gensalt(rounds=12)
#     hashed = bcrypt.hashpw(password, salt)
#     return hashed,salt 

#   def alternateCheck(self,password,hashed,saltedString=""):
#     if bcrypt.checkpw(password, hashed):
#       return True
#     else:
#       return False





 
# if __name__ == "__main__":

#   pwd = AdaptableHash()
#   _, _,h,s = pwd.GenerateHashANDSalt("qwerty")
#   print(h)
#   password = "qwerty"
#   print(pwd.compareHash(password, h))
#   password = "qwerty1"
#   print(pwd.compareHash(password, h))