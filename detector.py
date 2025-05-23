import sys
sys.path.insert(0, './YOLOX')
import torch
import numpy as np
import cv2

from YOLOX.yolox.data.data_augment import preproc
from YOLOX.yolox.data.datasets import COCO_CLASSES
from YOLOX.yolox.exp.build import get_exp_by_name,get_exp_by_file
from YOLOX.yolox.utils import postprocess
from utils.visualize import vis



COCO_MEAN = (0.485, 0.456, 0.406)
COCO_STD = (0.229, 0.224, 0.225)




class Detector():
    def __init__(self, model='yolox-s', ckpt='yolox_s.pth.tar'):
        super(Detector, self).__init__()



        self.device = torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
        self.device = torch.device('cpu')
        self.exp = get_exp_by_name(model)
        self.test_size = self.exp.test_size
        self.model = self.exp.get_model()
        self.model.to(self.device)
        self.model.eval()
        checkpoint = torch.load(ckpt, map_location="cpu")
        self.model.load_state_dict(checkpoint["model"])



    def detect(self, raw_img, visual=True, conf=0.5):
        info = {}
        img, ratio = preproc(raw_img, self.test_size, COCO_MEAN, COCO_STD)
        info['raw_img'] = raw_img
        info['img'] = img

        img = torch.from_numpy(img).unsqueeze(0)
        img = img.to(self.device)

        with torch.no_grad():
            outputs = self.model(img)
            outputs = postprocess(
                outputs, self.exp.num_classes, self.exp.test_conf, self.exp.nmsthre  
            )[0].cpu().numpy()
        
        if outputs[0] is None:
            info['boxes'], info['scores'], info['class_ids'],info['box_nums']=None,None,None,0
        else:
            info['boxes'] = outputs[:, 0:4]/ratio
            info['scores'] = outputs[:, 4] * outputs[:, 5]
            info['class_ids'] = outputs[:, 6]

            mask = info['scores']>=conf
            info['boxes'] =  info['boxes'][mask]
            info['scores'] =  info['scores'][mask]
            info['class_ids'] =  info['class_ids'][mask]
            info['box_nums'] = mask.sum()
            
        if visual:
            info['visual'] = vis(info['raw_img'], info['boxes'], info['scores'], info['class_ids'], conf, COCO_CLASSES)
        return info






if __name__=='__main__':
    detector = Detector()
    img = cv2.imread('dog.jpg')
    img_,out = detector.detect(img)
    print(out)
