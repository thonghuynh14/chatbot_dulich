import chromadb
from chromadb import PersistentClient
import numpy as np
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, util
from pyvi.ViTokenizer import tokenize
import pandas as pd
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sentence_transformers import SentenceTransformer

class LocalChromaDB():
    client = PersistentClient(path="dulich_db")
    model = SentenceTransformer("VoVanPhuc/sup-SimCSE-VietNamese-phobert-base")
    sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
            model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
        )

    def __init__(self):
        pass

    def check_db(self):
        '''
        Check whether database exists
        '''
        if self.client.list_collections():
            print('client exist!')
            return True
        else:
            print("client doesn't exist")
            return False

    def extract_question_data_adapter(self,
            link_data: str,
            is_save: bool=True
        ):
        '''
        Extract neccessary fields of questions to create chroma database
        Args:
            - link_data (str): link to excel file
            - is_save (bool): whether to save preprocessed data into csv file
        '''
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        index = 0
        dataset = pd.read_excel(link_data)
        dataset['Tổng hợp'] = ""
        self.data = dataset["Câu hỏi"]
        if link_data == "data/datacauhoitonghopv1.xlsx":
            for index, row in dataset.iterrows():
                dataset.loc[index, 'Tổng hợp'] = "Câu hỏi: {} /n trả lời: {}".format(row["Câu hỏi"], row["Trả lời"])
                documents.append(row['Câu hỏi'])
                embedding = self.model.encode(row['Câu hỏi']).tolist()
                embeddings.append(embedding)
                metadatas.append({'source': row['ĐỊA ĐIỂM'],'trả lời': row["Trả lời"]})
                ids.append(str(index + 1))
            if is_save:
                dataset.to_excel("data/DataChatbotdulich.xlsx")
        return documents, embeddings, metadatas, ids
    
    def create_db_summary(self, 
            link_data: str, 
            name_collection: str
        ):
        '''
        Create database for Vietnam Literary Story summary
        Args:
            - link_data (str): link of excel file including the neccessary information to save in collection.
            - name_collection (str): name of chroma database collection.
        '''
        documents, embeddings, metadatas, ids= self.extract_question_data_adapter(link_data)
        dulich_collection = self.client.create_collection(name=name_collection,
                                                    metadata={"hnsw:space": "cosine"},
                                                    embedding_function=self.sentence_transformer_ef)
        dulich_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("Data has been added in collection {}".format(name_collection))
    
    def find_sim_queries(self,
            name_collection: str,
            name_diadiem: str, 
            question: str,
            num_of_answer:int=1
        ):
        '''
        Finding similarity queries
        Args:
            - name_collection (str): Name of collection
            - story_name (str): The story name to limit the scope of searching similar queries
            - question (str): The input question
            - num_of_answer (int): Number of return similar queries 
        '''
        dulich_collection = self.client.get_collection(
            name=name_collection,
            embedding_function=self.sentence_transformer_ef)
        
        results = dulich_collection.query(
            query_texts=[question],
            n_results=num_of_answer,
            where_document={"$contains":name_diadiem}
        )

        for i in results['documents'][0]:
            print('Relevant Query: ', i)
        return results['documents']
        
    def find_score_answer(self, query):
        embeddings_search_cauhoi = np.load("embedding_cauhoi/question_embedding.npy")
        question_embedding = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(question_embedding, embeddings_search_cauhoi, top_k=1)
        hits = hits[0]
        for hit in hits:
            temp = hit['score']
            print(temp)
            return temp
        
    def find_sim_answer(
            self,
            name_collection: str,
            name_diadiem: str, 
            question: str,
            num_of_answer:int=1
        ):
        '''
        Finding similarity queries
        Args:
            - name_collection (str): Name of collection
            - story_name (str): The story name to limit the scope of searching similar queries
            - question (str): The input question
            - num_of_answer (int): Number of return similar queries 
        '''
        dulich_collection = self.client.get_collection(
            name=name_collection,
            embedding_function=self.sentence_transformer_ef)
        
        results = dulich_collection.query(
            query_texts=[question],
            n_results=num_of_answer,
            where_document={"$contains": name_diadiem}
        )
        sim_score = self.find_score_answer(query=question)
        
        if sim_score >= 0.5:
          relevant_answers = results['metadatas'][0]
          if relevant_answers:
              first_answer = relevant_answers[0]
              answer = first_answer.get('trả lời', 'N/A')
              # print('Relevant Answer (Trả lời):', answer)
              return answer
        else:
            pre_announce = "Rất xin lỗi, dường như câu hỏi của bạn chưa thực sự rõ ràng hoặc câu hỏi vượt quá phạm vi của tôi ở '{}'. Có phải bạn muốn hỏi một trong các câu hỏi sau đây ?".format(name_diadiem)
            similar_questions = self.find_sim_queries(
                name_collection=name_collection,
                name_diadiem=name_diadiem,
                question=question,
                num_of_answer=3
            )
            similar_question_list =  [f"<br>{idx + 1}) {similar_question}" for idx, similar_question in enumerate(similar_questions[0])]
            similar_question_list = ''.join(similar_question_list)
            similar_question_list = pre_announce + str(similar_question_list)
            return similar_question_list

if __name__ == "__main__":
    # 1. Test creating chromadb
    link_data="data/datacauhoitonghopv1.xlsx"
    name_data = "dulich_simcse"
    chromadb = LocalChromaDB()
    chromadb.create_db_summary(link_data, name_data)
    chromadb.check_db()
    # # 2. Test query question
    # chromadb = LocalChromaDB()
    # similar_queries = chromadb.find_sim_queries(
    #     name_collection='dulich_simcse',
    #     name_diadiem='Huế',
    #     question='Tôi muốn tìm phòng giá 500k tại Huế',
    #     num_of_answer=3
    # )

    # # 3. Test the answer
    # chromadb = LocalChromaDB()
    # similar_queries = chromadb.find_sim_answer(
    #     name_collection='dulich_simcse',
    #     name_diadiem='Huế',
    #     question='Khách sạn giá 500k',
    #     num_of_answer=1
    # )