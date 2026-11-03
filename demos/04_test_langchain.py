import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
OPENAI_API_KEY = os.getenv('ALI_BAILIAN_API_KEY')
OPENAI_API_MODEL = os.getenv('ALI_BAILIAN_MODEL')
print('这是key：', OPENAI_API_KEY)

model = ChatOpenAI(model=OPENAI_API_MODEL)
messages = [
    SystemMessage(content="Translate the following from English into Italian"),
    HumanMessage(content="hi!"),
]
model.invoke(messages)

from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
result = model.invoke(messages)
parser.invoke(result)