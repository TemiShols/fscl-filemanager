import langchain
import os
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains.summarize import load_summarize_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chat_models import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.prompt_template import format_document
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import Docx2txtLoader, PyPDFLoader, UnstructuredExcelLoader
from tempfile import NamedTemporaryFile
import chardet


def summarize_doc(file_field):
    try:
        file_path = file_field.path
        with open(file_path, 'rb') as file:
            content = file.read()
        result = chardet.detect(content)
        encoding = result['encoding']
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            document_content = file.read()
        if file.name.split('.')[-1] == 'docs':
            loader = Docx2txtLoader(file_path)
            data = loader.load()
            print(data)
            #   llm = OpenAI(openai_api_key='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')
            llm = ChatOpenAI(openai_api_key='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',temperature=0, model_name="gpt-3.5-turbo-16k")
            chain = load_summarize_chain(llm, chain_type="stuff")

            result = chain.run(data)
            return result
        elif file.name.split('.')[-1] == 'pdf':
            loader = PyPDFLoader(file_path)
            data = loader.load_and_split()
            #   llm = OpenAI(openai_api_key='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')
            llm = ChatOpenAI(openai_api_key='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',temperature=0, model_name="gpt-3.5-turbo-16k")
            chain = load_summarize_chain(llm, chain_type="stuff")

            result = chain.run(data)
            return result
        elif file.name.split('.')[-1] == 'xlsx':
            loader = UnstructuredExcelLoader(file_path)
            data = loader.load()
            #   llm = OpenAI(openai_api_key='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')
            llm = ChatOpenAI(openai_api_key='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',temperature=0, model_name="gpt-3.5-turbo-16k")
            chain = load_summarize_chain(llm, chain_type="stuff")
            result = chain.run(data)
            return result
    except Exception as e:
        return f"Error summarizing document: {e}"