# 소스코드 업데이트
git pull

# 도커 이미지 빌드 및 새로 만들어진 이미지로 서버 재시작
docker build -t oxygen .
docker rm -f oxygen
docker run -d -p 10443:10443 --name oxygen oxygen:latest

# 리버스 프록시 서버에도 반영
docker rm -f caddy
docker run -d -p 80:80/tcp -p 443:443/tcp -p 2019:2019/tcp -v C:\ServerPackage\Scoreboard\caddy_conf:C:\etc\caddy --name caddy caddy:latest

# 기존에 사용하지 않는 도커 이미지 삭제
docker image prune