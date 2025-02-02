import joblib
import json
import numpy as np
import base64
import cv2
import pywt   

def rectangleImage(img):
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier('./opencv/data/haarcascades/haarcascade_frontalface_default.xml')
    img = cv2.imread(img)
    faces = face_cascade.detectMultiScale(img, 1.3, 5)
    for face in faces:
        (x,y,w,h) = face
        face_img = cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),4)
    return face_img

def w2d(img, mode='haar', level=1):
    imArray = img
    #Datatype conversions
    #convert to grayscale
    imArray = cv2.cvtColor( imArray,cv2.COLOR_RGB2GRAY )
    #convert to float
    imArray =  np.float32(imArray)   
    imArray /= 255
    # compute coefficients 
    coeffs=pywt.wavedec2(imArray, mode, level=level)

    #Process Coefficients
    coeffs_H = list(coeffs)  
    coeffs_H[0] *= 0  

    # reconstruction
    imArray_H=pywt.waverec2(coeffs_H, mode);
    imArray_H *= 255
    imArray_H =  np.uint8(imArray_H)

    return imArray_H

__class_name_to_number = {}
__class_number_to_name = {}

__model = None

def classify_image(image_base64_data, file_path=None):

    imgs = get_cropped_image_if_2_eyes(file_path, image_base64_data)

    result = []
    for img in imgs:
        scalled_raw_img = cv2.resize(img, (32, 32))
        img_har = w2d(img, 'db1', 5)
        scalled_img_har = cv2.resize(img_har, (32, 32))
        combined_img = np.vstack((scalled_raw_img.reshape(32 * 32 * 3, 1), scalled_img_har.reshape(32 * 32, 1)))

        len_image_array = 32*32*3 + 32*32

        final = combined_img.reshape(1,len_image_array).astype(float)
        result.append({
            'class': class_number_to_name(__model.predict(final)[0]),
            'class_probability': np.around(__model.predict_proba(final)*100,2).tolist()[0],
            'class_dictionary': __class_name_to_number
        })

    return result

def class_number_to_name(class_num):
    return __class_number_to_name[class_num]

def load_saved_artifacts():
    print("loading saved artifacts...start")
    global __class_name_to_number
    global __class_number_to_name

    with open("./class_dictionary.json", "r") as f:
        __class_name_to_number = json.load(f)
        __class_number_to_name = {v:k for k,v in __class_name_to_number.items()}

    global __model
    if __model is None:
        with open('./saved_model.pkl', 'rb') as f:
            __model = joblib.load(f)
    print("loading saved artifacts...done")

def get_cv2_image_from_base64_string(b64str):
    '''
    credit: https://stackoverflow.com/questions/33754935/read-a-base-64-encoded-image-from-memory-using-opencv-python-library
    :param uri:
    :return:
    '''
    encoded_data = b64str.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def get_cropped_image_if_2_eyes(image_path, image_base64_data):
    face_cascade = cv2.CascadeClassifier('./opencv/data/haarcascades/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('./opencv/data/haarcascades/haarcascade_eye.xml')
    
    if image_path:
        img = cv2.imread(image_path)
    else:
        img = get_cv2_image_from_base64_string(image_base64_data)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    cropped_faces = []
    for (x,y,w,h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = img[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            if len(eyes) >= 2:
                cropped_faces.append(roi_color)
    return cropped_faces

def get_b64_test_image_for_virat():
    with open("b64.txt") as f:
        return f.read()

if __name__ == '__main__':
    load_saved_artifacts()

    #print(classify_image(get_b64_test_image_for_virat(), None))

    #print(classify_image(None, './testImg/MAROC_TOP_10.jpg'))
    #print(classify_image(None, './test_images\pic1.png'))


import streamlit as st
import base64
from PIL import Image
import tempfile

st.markdown('<h1 style="color:white;">Face Recognition App</h1>', unsafe_allow_html=True)
st.markdown('<h2 style="color:#D1F4FF;">The model classifies image into following categories:</h2>', unsafe_allow_html=True)
st.markdown('<h3 style="color:white;"> bono,  ounahi, ziach, hakimi, Amrabt</h3>', unsafe_allow_html=True)

# background image to streamlit
@st.cache_data
#S@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file) 
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: scroll; # doesn't work
    }
    </style>
    ''' % bin_str
    
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return

set_png_as_page_bg("./face.webp")
st.write("<h4 style='color: white; font-size: 16px;'>Insert image for classification</h3>", unsafe_allow_html=True)
upload= st.file_uploader('insert image for classification', type=['png','jpg'], key='file_uploader')
c1, c, c2= st.columns(3)
if upload is not None:
  with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(upload.read())
        file_url = tmp_file.name
  im= Image.open(upload)
  img= np.asarray(im)
  image= cv2.resize(img,(224, 224))
  #img= preprocess_input(image)
  img= np.expand_dims(img, 0)
  c1.markdown("<h4 style='color: white;'>Input Image</h2>", unsafe_allow_html=True)
  #c1.header('Input Image')
  c1.image(im)
  


  imageRec = rectangleImage(file_url)
  imgR= np.asarray(imageRec)
  image= cv2.resize(imgR,(224, 224))
  img= np.expand_dims(image, 0)
  c.markdown("<h4 style='color: white;'>Output</h2>", unsafe_allow_html=True)
  #c.header('Output')
  c.image(img) 
  # prediction on model
  #c2.header('<span style="color: white;">Detected person(s):</span>', unsafe_allow_html=True)
  #c2.subheader() 
  c2.markdown("<h4 style='color: white;'>Detected person(s):</h2>", unsafe_allow_html=True)
  listItem = classify_image(None, file_url)
  for item in listItem:
    class_name = '         '+item['class']
    c2.write(f'<span style="font-size: 22px; color: pink; font-weight: bold; text-shadow: 5px 5px 5px #000000;">{class_name}</span>', unsafe_allow_html=True)
    #c2.write(f'<span style="font-size: 22px; color: #E4F6FB;">{class_name}</span>', unsafe_allow_html=True)


