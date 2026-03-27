FROM nginx:alpine
# Remove default config
RUN rm /etc/nginx/conf.d/default.conf
# Copy our dev config
COPY nginx/dev.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
