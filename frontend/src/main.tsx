import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// 카카오 맵 SDK 동적 로드
const loadKakaoMapScript = () => {
  const kakaoMapKey = import.meta.env.VITE_KAKAO_MAP_KEY;
  
  if (!kakaoMapKey) {
    console.error('❌ VITE_KAKAO_MAP_KEY 환경 변수가 설정되지 않았습니다.');
    return;
  }

  const script = document.createElement('script');
  script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoMapKey}&autoload=false`;
  script.async = true;
  document.head.appendChild(script);
};

loadKakaoMapScript();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
