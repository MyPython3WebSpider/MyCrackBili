import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ACCOUNT = ''
PASSWORD = ''
BORDER = 22


class CrackBili():
    def __init__(self):
        self.url = 'https://passport.bilibili.com/login'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 10)
        self.account = ACCOUNT
        self.password = PASSWORD

    def __del__(self):
        self.browser.close()

    def open(self):
        """
        打开网页输入用户名密码
        :return:
        """
        self.browser.get(self.url)
        account = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'login-passwd')))
        account.send_keys(self.account)
        password.send_keys(self.password)

    def get_bili_button(self):
        """
        获取初始验证码按钮
        :return:
        """
        # button = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gt_widget gt_clean gt_hide')))
        button = self.browser.find_element_by_xpath('//*[@id="gc-box"]/div/div[3]/div[2]')
        return button

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="gc-box"]/div/div[@class="gt_widget gt_clean gt_show"]')))
        # img = self.browser.find_element_by_xpath('//*[@id="gc-box"]/div/div[1]')
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return top, bottom, left, right

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        # BytesIO(screenshot) 写入内存的二进制文件
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'gt_widget gt_clean gt_show')))
        return slider

    def get_geetest_image(self, name='captcha.png'):
        """
        获取验证码图片
        :param name:
        :return:  图片验证码
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha

    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 不带缺口图片
        :param image2:  带缺口图片
        :return:
        """
        left = 80
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素点是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 获取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 3 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 4

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 10
            else:
                a = -8
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider:滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def login(self):
        """
        登录
        :return:
        """
        submit = self.browser.find_element_by_class_name('btn-login')
        submit.click()
        time.sleep(5)
        print('登录成功')

    def crack(self):
        # 输入用户名，密码
        self.open()
        # 获取验证码按钮
        button = self.get_bili_button()
        # 移动到验证码按钮，悬浮
        ActionChains(self.browser).move_to_element(button).perform()
        # 获取原始验证码图片
        image1 = self.get_geetest_image('captcha1.png')
        button.click()
        time.sleep(3)
        # 获取带缺口的验证码图片
        image2 = self.get_geetest_image('captcha2.png')
        # print(image2.size)
        # 获取缺口位置
        gap = self.get_gap(image1, image2)
        print('缺口位置', gap)
        gap -= BORDER
        track = self.get_track(gap)
        print('滑动轨迹', track)
        # ActionChains(self.browser).click_and_hold(button).perform()
        self.move_to_gap(button, track)

        try:
            success = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="gc-box"]//div[@class="gt_info_tip gt_success"]'))
            )
        except Exception as e:
            success = False
        # print(success)
        if not success:
            self.crack()
        else:
            self.login()


if __name__ == '__main__':
    cb = CrackBili()
    cb.crack()



