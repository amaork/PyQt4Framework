# -*- coding: utf-8 -*-
from types import StringTypes
from PySide.QtGui import QMessageBox

__all__ = ['showQuestionBox', 'showMessageBox',
           'MB_TYPES', 'MB_TYPE_ERR', 'MB_TYPE_INFO', 'MB_TYPE_WARN', 'MB_TYPE_QUESTION']

# Message box types
MB_TYPE_ERR = "error"
MB_TYPE_INFO = "info"
MB_TYPE_WARN = "warning"
MB_TYPE_QUESTION = "question"
MB_TYPES = (MB_TYPE_ERR, MB_TYPE_INFO, MB_TYPE_WARN, MB_TYPE_QUESTION)


def showQuestionBox(parent, title, context):
    """ Show a Question message box and return result

    :param parent: Message parent
    :param title: Message title
    :param context: Message title
    :return: if press ok return true, else return false
    """

    # Type check
    if not isinstance(title, StringTypes) or not isinstance(context, StringTypes):
        return False

    ret = QMessageBox.question(parent, parent.tr(title), parent.tr(context), QMessageBox.Ok | QMessageBox.Cancel)

    return False if ret == QMessageBox.Cancel else True


def showMessageBox(parent, msg_type, title, context, result=False):
    """Show a QMessage box

    :param parent: Message box parent
    :param msg_type: Message type
    :param title: Message title
    :param context: Message context
    :param result: result
    :return: result
    """

    # Type check
    if msg_type not in MB_TYPES or not isinstance(title, StringTypes) or not isinstance(context, StringTypes):
        return False

    if msg_type == MB_TYPE_INFO:
        result = True
        QMessageBox.information(parent, parent.tr(title), parent.tr(context))
    elif msg_type == MB_TYPE_ERR:
        QMessageBox.critical(parent, parent.tr(title), parent.tr(context))
    elif msg_type == MB_TYPE_WARN:
        QMessageBox.warning(parent, parent.tr(title), parent.tr(context))
    elif msg_type == MB_TYPE_QUESTION:
        return showQuestionBox(parent, title, context)

    return result
