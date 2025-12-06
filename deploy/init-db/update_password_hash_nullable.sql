-- password_hash를 nullable로 변경 (소셜 로그인 지원)
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

COMMENT ON COLUMN users.password_hash IS '비밀번호 해시 (소셜 로그인 사용자는 NULL)';


