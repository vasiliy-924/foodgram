# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./

# RUN npm install # в Крыму это скачивание заблокировано
RUN npm config set registry https://registry.npmmirror.com \
    && npm cache clean --force \
    && npm install

COPY . ./
RUN npm run build

CMD cp -r build result_build
