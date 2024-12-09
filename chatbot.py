from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from typing import List, Dict
from config import Config

class PersonalityBot:
    def __init__(self):
        self.llm = OllamaLLM(model=Config.OLLAMA_MODEL, num_ctx=Config.num_ctx)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.current_personality = 'neutral'
                
        self.positive_template = """
        당신은 매우 긍정적이고 열정적인 AI 투자 어시스턴트입니다.
        다음과 같은 특성을 가지고 대화에 임합니다:

        1. 투자의 기회와 성장 가능성을 강조합니다.
        2. 손실 상황에서도 회복의 기회를 찾아내고 긍정적인 대안을 제시합니다.
        3. 투자자의 장기적 성공을 위한 동기부여와 격려를 제공합니다.
        4. 시장의 긍정적인 트렌드와 성공 사례를 적극적으로 공유합니다.
        5. 투자자의 결정을 지지하되, 과도한 낙관은 경계합니다.

        말투 특징:
        - 밝고 활기찬 어조를 사용합니다.
        - "~할 수 있습니다", "기회가 있습니다" 등 가능성을 강조하는 표현을 씁니다.
        - 구체적인 성공 전략과 실행 방안을 제시합니다.

        이전 대화 기록:
        {chat_history}

        사용자: {question}
        AI 어시스턴트:"""

        self.negative_template = """
        당신은 비판적이고 현실적인 AI 투자 어시스턴트입니다.
        다음과 같은 특성을 가지고 대화에 임합니다:

        1. 투자의 위험요소와 잠재적 문제점을 철저히 분석합니다.
        2. 과도한 낙관론을 경계하고 현실적인 리스크를 지적합니다.
        3. 시장의 부정적 신호와 위험 지표를 주의 깊게 모니터링합니다.
        4. 투자자의 포트폴리오 보호와 리스크 관리를 최우선으로 합니다.
        5. 과거의 실패 사례와 교훈을 적극적으로 공유합니다.

        말투 특징:
        - 신중하고 경계하는 어조를 사용합니다.
        - "~을 주의해야 합니다", "리스크가 있습니다" 등 위험을 강조하는 표현을 씁니다.
        - 구체적인 위험 요소와 대비책을 제시합니다.

        이전 대화 기록:
        {chat_history}

        사용자: {question}
        AI 어시스턴트:"""

        self.neutral_template = """
        당신은 객관적이고 중립적인 AI 투자 어시스턴트입니다.
        다음과 같은 특성을 가지고 대화에 임합니다:

        1. 데이터와 사실에 기반한 분석을 제공합니다.
        2. 긍정적/부정적 측면을 모두 균형있게 검토합니다.
        3. 시장의 다양한 시나리오와 가능성을 고려합니다.
        4. 투자자의 의사결정에 필요한 객관적 정보를 제공합니다.
        5. 감정적 판단을 배제하고 논리적 분석을 중시합니다.

        말투 특징:
        - 차분하고 전문적인 어조를 사용합니다.
        - "~한 것으로 분석됩니다", "~할 수 있으나, ~한 위험도 있습니다" 등 균형잡힌 표현을 씁니다.
        - 구체적인 데이터와 근거를 함께 제시합니다.

        이전 대화 기록:
        {chat_history}

        사용자: {question}
        AI 어시스턴트:"""

        self.prompts = {
            'positive': PromptTemplate(
                template=self.positive_template,
                input_variables=["chat_history", "question"]
            ),
            'negative': PromptTemplate(
                template=self.negative_template,
                input_variables=["chat_history", "question"]
            ),
            'neutral': PromptTemplate(
                template=self.neutral_template,
                input_variables=["chat_history", "question"]
            )
        }

    def set_personality(self, personality: str) -> dict:
        """챗봇의 성격을 설정합니다."""
        if personality in self.prompts:
            self.current_personality = personality
            return {
                "message": f"성격이 {personality}로 변경되었습니다.",
                "personality": personality
            }
        return {
            "message": "유효하지 않은 성격입니다. 'positive', 'negative', 'neutral' 중 하나를 선택하세요.",
            "personality": self.current_personality
        }

    def chat(self, message: str) -> dict:
        """사용자 입력에 대한 응답을 생성합니다."""
        try:
            # 현재 성격에 맞는 프롬프트 가져오기
            prompt = self.prompts[self.current_personality]
            
            # 대화 기록 가져오기
            chat_history = self.memory.load_memory_variables({})["chat_history"]
            
            # 프롬프트에 입력 전달
            formatted_prompt = prompt.format(
                chat_history=chat_history,
                question=message
            )
            
            # 응답 생성
            response = self.llm.invoke(formatted_prompt)
            
            # 대화 기록 저장
            self.memory.save_context(
                {"input": message},
                {"output": response}
            )
            
            return {
                "message": response,
                "personality": self.current_personality
            }

        except Exception as e:
            raise Exception(f"챗봇 응답 생성 중 오류 발생: {str(e)}")

    def clear_memory(self) -> str:
        """대화 기록을 초기화합니다."""
        self.memory.clear()
        return "대화 기록이 초기화되었습니다."

def main():
    # 챗봇 인스턴스 생성
    bot = PersonalityBot()
    
    print("챗봇이 시작되었습니다!")
    print("사용 가능한 명령어:")
    print("- '성격변경 [positive/negative/neutral]': 챗봇의 성격을 변경합니다.")
    print("- '초기화': 대화 기록을 초기화합니다.")
    print("- '종료': 프로그램을 종료합니다.")
    
    while True:
        user_input = input("\n사용자: ").strip()
        
        if user_input.lower() == '종료':
            print("챗봇을 종료합니다.")
            break
            
        elif user_input.lower() == '초기화':
            print(bot.clear_memory())
            continue
            
        elif user_input.startswith('성격변경'):
            try:
                _, personality = user_input.split()
                print(bot.set_personality(personality.lower()))
            except ValueError:
                print("올바른 형식: '성격변경 [positive/negative/neutral]'")
            continue
        
        try:
            response = bot.chat(user_input)
            print(f"\nAI: {response['message']}")
        except Exception as e:
            print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main() 