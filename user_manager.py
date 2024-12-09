import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import shutil
import logging
from config import Config

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        """사용자 관리자 초기화"""
        self.users = {}
        self.next_user_id = 1
        self.load_users()
        
    def load_users(self):
        """사용자 데이터 로드"""
        try:
            if os.path.exists(Config.USERS_FILE):
                with open(Config.USERS_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                    logger.info(f"Loaded {len(self.users)} users from file")
                    
                # 다음 사용자 ID 설정
                if self.users:
                    self.next_user_id = max(int(user_id) for user_id in self.users.keys()) + 1
                    
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            self._restore_from_backup()
    
    def _create_backup(self):
        """현재 사용자 데이터의 백업 생성"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(Config.BACKUP_DIR, f'users_{timestamp}.json')
            
            # 현재 파일을 백업
            if os.path.exists(Config.USERS_FILE):
                shutil.copy2(Config.USERS_FILE, backup_file)
                
                # 오래된 백업 파일 제거
                backup_files = sorted([f for f in os.listdir(Config.BACKUP_DIR) if f.startswith('users_')])
                while len(backup_files) > Config.MAX_BACKUP_COUNT:
                    os.remove(os.path.join(Config.BACKUP_DIR, backup_files.pop(0)))
                    
                logger.info(f"Backup created: {backup_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False
    
    def _restore_from_backup(self):
        """가장 최근 백업에서 복구"""
        try:
            backup_files = sorted([f for f in os.listdir(Config.BACKUP_DIR) if f.startswith('users_')])
            if backup_files:
                latest_backup = os.path.join(Config.BACKUP_DIR, backup_files[-1])
                with open(latest_backup, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"Restored from backup: {latest_backup}")
                return True
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            return False
    
    def save_users(self):
        """사용자 데이터 저장"""
        try:
            # 백업 생성
            self._create_backup()
            
            # 임시 파일에 저장
            temp_file = f"{Config.USERS_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            
            # 파일 교체
            os.replace(temp_file, Config.USERS_FILE)
            logger.info(f"Saved {len(self.users)} users")
            return True
            
        except Exception as e:
            logger.error(f"Error saving users: {str(e)}")
            return False
    
    def create_user(self, username, password):
        """새 사용자 생성"""
        try:
            # 입력값 검증
            if len(username) < Config.MIN_USERNAME_LENGTH:
                return None, "사용자명이 너무 짧습니다."
            if len(password) < Config.MIN_PASSWORD_LENGTH:
                return None, "비밀번호가 너무 짧습니다."
            
            # 사용자 수 제한 확인
            if len(self.users) >= Config.MAX_USERS:
                return None, "최대 사용자 수에 도달했습니다."
            
            # 중복 확인
            if self.is_username_taken(username):
                return None, "이미 사용 중인 사용자명입니다."
            
            user_id = str(self.next_user_id)
            user = {
                'id': user_id,
                'username': username,
                'password': generate_password_hash(password),
                'balance': Config.INITIAL_BALANCE,
                'stocks': {},
                'total_value': Config.INITIAL_BALANCE,
                'total_return': 0,
                'trade_count': 0,
                'created_at': datetime.now().isoformat()
            }
            
            self.users[user_id] = user
            self.next_user_id += 1
            
            if self.save_users():
                logger.info(f"User created: {username}")
                return {'id': user_id, 'username': username}, None
            else:
                return None, "사용자 데이터 저장에 실패했습니다."
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None, "사용자 생성 중 오류가 발생했습니다."
    
    def authenticate_user(self, username, password):
        """사용자 인증"""
        try:
            for user_id, user in self.users.items():
                if user['username'] == username:
                    if check_password_hash(user['password'], password):
                        logger.info(f"User authenticated: {username}")
                        return {'id': user_id, 'username': username}, None
            return None, "아이디 또는 비밀번호가 잘못되었습니다."
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None, "인증 중 오류가 발생했습니다."
    
    def get_user(self, user_id):
        """사용자 정보 조회"""
        return self.users.get(str(user_id))
    
    def is_username_taken(self, username):
        """사용자명 중복 확인"""
        return any(user['username'] == username for user in self.users.values())
    
    def update_user(self, user_id, data):
        """사용자 정보 업데이트"""
        try:
            user_id = str(user_id)
            if user_id in self.users:
                self.users[user_id].update(data)
                if self.save_users():
                    logger.info(f"User updated: {user_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False 