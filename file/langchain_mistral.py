import os
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationBufferWindowMemory
import nest_asyncio
from django.conf import settings
from .models import Project, Document as Dokument
from langchain.schema import Document

nest_asyncio.apply()

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = settings.HF_HUB_DISABLE_SYMLINKS_WARNING
os.environ["HF_TOKEN"] = settings.HF_TOKEN
os.environ['KMP_DUPLICATE_LIB_OK'] = settings.KMP_DUPLICATE_LIB_OK
chat_model = ChatMistralAI(mistral_api_key=settings.MISTRAL_API_KEY)


def process_langchain_rag(doc_id, query):
    try:
        doc = Dokument.objects.get(pk=doc_id)
    except Dokument.DoesNotExist:
        raise ValueError(f"Project not found: {doc_id}")

    # Create a Document directly from the project content
    docs = [Document(page_content=doc.content, metadata={"source": f"project_{doc_id}"})]
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)
    #   embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    embedding_function = FastEmbedEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create the vector store

    vector_store = Chroma.from_documents(documents, embedding_function)
    retriever = vector_store.as_retriever()

    # Define LLM
    model = chat_model
    #   add memory so that our conversation can be remembered across subsequent queries
    #   memory = ConversationBufferWindowMemory(
    #   memory_key='chat_history',
    #   return_messages=True,
    #   k=3
    #   )
    # Define prompt template
    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions based on provided context. 
    If the context does not contain enough information to answer the question, 
    use your general knowledge to assist.

    Here is the context you have:
    <context>
    {context}
    </context>

    Please use the context to answer the following question. 
    If the context does not provide enough information, 
    supplement it with your own understanding:

    Question: {input}

    Answer:
    """)

    # Create a retrieval chain to answer questions
    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain, )
    response = retrieval_chain.invoke({"input": query})
    #   conversation = ConversationalRetrievalChain.from_llm(
    #   llm=model,
    #   retriever=retriever,
    #   memory=memory,
    #   max_tokens_limit=1536,
    #   prompt=prompt,
    #   )
    #   response = conversation.invoke({"input": query})
    return response["answer"]


def process_langchain_rag_project(proj_id, query):
    try:
        proj = Project.objects.get(pk=proj_id)
    except Project.DoesNotExist:
        raise ValueError(f"Project not found: {proj_id}")

        # Create a Document directly from the project content
    docs = [Document(page_content=proj.content, metadata={"source": f"project_{proj_id}"})]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    #   embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    embedding_function = FastEmbedEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(documents, embedding_function)
    retriever = vector_store.as_retriever()

    model = chat_model

    #   memory = ConversationBufferWindowMemory(
    #   memory_key='chat_history',
    #   return_messages=True,
    #   k=3
    #   )

    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions based on provided context. 
    If the context does not contain enough information to answer the question, 
    use your general knowledge to assist.

    Here is the context you have:
    <context>
    {context}
    </context>

    Please use the context to answer the following question. 
    If the context does not provide enough information, 
    supplement it with your own understanding:

    Question: {input}

    Answer:
    """)

    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({"input": query})

    #   conversation = ConversationalRetrievalChain.from_llm(
    #   llm=model,
    #   retriever=retriever,
    #   memory=memory,
    #   max_tokens_limit=1536,
    #   combine_docs_chain_kwargs={"prompt": prompt},
    #   )
    #   response = conversation({"input": query})
    return response["answer"]


def process_langchain_rag_project2(proj_id, query):
    try:
        proj = Project.objects.get(pk=proj_id)
    except Project.DoesNotExist:
        raise ValueError(f"Project not found: {proj_id}")

        # Create a Document directly from the project content
    docs = [Document(page_content=proj.content, metadata={"source": f"project_{proj_id}"})]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(documents, embedding_function)
    retriever = vector_store.as_retriever()

    model = chat_model

    memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        return_messages=True,
        k=3
    )

    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions based on provided context. 
    If the context does not contain enough information to answer the question, 
    use your general knowledge to assist.
    Here is the context you have:
    {context}
    Chat History: {chat_history}
    Human: {question}
    AI: """)

    #   document_chain = create_stuff_documents_chain(model, prompt)
    #   retrieval_chain = create_retrieval_chain(retriever, document_chain)
    #   response = retrieval_chain.invoke({"input": query})

    qa_chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    conversation = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
        question_generator=LLMChain(llm=model, prompt=prompt),
        combine_docs_chain=qa_chain
    )
    response = conversation({"question": query})
    return response["answer"]
