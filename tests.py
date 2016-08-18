# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest
import time
import os
from app import db
from app.models import Category


class Testcase(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def check_status(self, test_correct, search_message):
        """
        Функция проверяет статус задачи и сравнивает его с эталонным

        :param test_correct:  Задача должна завершиться успешно или нет
        :param search_message: Сообщение, которое должно вернуть приложение
        :return: Если статус или сообщение не совпадают с эталонным, то ставить тесту статус "Не пройден"
        """
        driver = self.driver
        # Цикл для ожидания завершения задачи
        for i in range(60):
            status_success = ''
            status_fail = ''
            try:
                status_success = driver.find_element_by_id("progressbar").get_attribute("testattribute")
            except:
                pass
            # Поиска сообщения в ответе приложения
            if status_success == 'suc':
                if test_correct:
                    if not (search_message in driver.find_element_by_id("upload_alert").text):
                        self.fail("incorrect")
                    return True
                else:
                    self.fail('incorrect')

            try:
                status_fail = driver.find_element_by_id("alert_container_fail").get_attribute("testattribute")
            except:
                pass
            if status_fail == 'fail':
                if not test_correct:
                    if not (search_message in driver.find_element_by_id("upload_alert").text):
                        self.fail("incorrect")
                    return True
                else:
                    self.fail('incorrect')

            time.sleep(1)
        self.fail('time out')

    def test_link_zip_file_correct(self):
        """
        Тест корректного zip-архива, скачиваемого по ссылке

        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_id("filename").clear()
        link = "http://spatialkeydocs.s3.amazonaws.com/FL_insurance_sample.csv.zip"
        driver.find_element_by_id("filename").send_keys(link)
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(True, 'Загрузка и разбор')

    def test_link_zip_file_bad(self):
        """
        Тест некорректного zip-архива, скачиваемого по ссылке
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_id("filename").clear()
        driver.find_element_by_id("filename").send_keys("http://www.colorado.edu/conflict/peace/download/peace.zip")
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(False, 'Неправильный формат zip-архива')

    def test_link_file_correct(self):
        """
        Тест корректного файла, скачиваемого по ссылке
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_id("filename").clear()
        driver.find_element_by_id("filename").send_keys(
            "http://samplecsvs.s3.amazonaws.com/Sacramentorealestatetransactions.csv")
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(True, 'Загрузка и разбор')

    def test_link_bad(self):
        """
        Тест некорректной ссылки
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_id("filename").clear()
        driver.find_element_by_id("filename").send_keys("incorrect link")
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(False, 'Неправильная ссылка')

    def test_disk_zip_file_bad(self):
        """
            Тест некорректного zip-файла, скачиваемого с диска
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.execute_script('document.getElementById("upload").style=""')
        driver.find_element_by_id("upload").clear()
        driver.find_element_by_id("upload").send_keys(
            os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files'), 'bad.zip'))
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(False, 'Неправильный формат архива')

    def test_disk_zip_file_correct(self):
        """
            Тест корректного zip-файла, скачиваемого с диска
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.execute_script('document.getElementById("upload").style=""')
        driver.find_element_by_id("upload").clear()
        driver.find_element_by_id("upload").send_keys(
            os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files'), 'good.zip'))
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(True, 'Загрузка и разбор')

    def test_disk_file_correct(self):
        """
            Тест корректного файла, скачиваемого с диска
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.execute_script('document.getElementById("upload").style=""')
        driver.find_element_by_id("upload").clear()
        driver.find_element_by_id("upload").send_keys(
            os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files'), 'good.csv'))
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(True, 'Загрузка и разбор')

    def test_disk_file_bad(self):
        """
            Тест некорректного файла, скачиваемого с диска
        :return:
        """
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.execute_script('document.getElementById("upload").style=""')
        driver.find_element_by_id("upload").clear()
        driver.find_element_by_id("upload").send_keys(
            os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files'), 'bad.csv'))
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(False, 'Ошибка кодировки')

    def test_database(self):
        """
            Тест на правильность количества вставляемых записей
        :return:
        """
        initial_count = db.session.query(Category.id).count()
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.execute_script('document.getElementById("upload").style=""')
        driver.find_element_by_id("upload").clear()
        driver.find_element_by_id("upload").send_keys(
            os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files'), 'test_count.csv'))
        driver.find_element_by_id("upload_file_btn").click()
        self.check_status(True, 'Загрузка и разбор')
        new_count = db.session.query(Category.id).count()
        self.assertEqual(new_count - initial_count, 9)

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException as e:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)


if __name__ == "__main__":
    unittest.main()
