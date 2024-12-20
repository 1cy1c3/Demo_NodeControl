import { api } from "./api";

export const login = async (email: string, password: string) => {
  const data = {"email": email,"password": password};
  const response = await api.post('/login', data);
  return response.data;
};

export const register = async (username: string, email: string, password: string) => {
  const data = {"username": username, "email": email, "password": password}
  const response = await api.post('/register', data);
  return response.data;
};

export const instanceSetup = async (userId: number,projectId: number) => {
  const data = {"user_id": userId, "project_id": projectId}
  const response = await api.post('/instance_setup', data);
  console.log(response.data, response.data.user_project_id);
  return response.data.user_project_id;
};

export const createWallet = async (network: string, userproductId: number) => {
  const data = {"wallet_type": network, "user_project_id": userproductId}
  const response = await api.post('/generate_wallet', data);
  return response.data.public_key;
};

export const setupProject = async (userProductId: number) => {
  const data = {"user_project_id": userProductId}
  const response = await api.post('/vps_setup', data);
  return response.data;
};

export const verifyEmail = async (token: string, email: string) => {
  const response = await api.get(`/verify_email?token=${token}&email=${email}`);
  return response.data;
};

export const getUserProjects = async (userId: number) => {
  const response = await api.get('/user_projects', { params: { user_id: userId } });
  return response.data;
};

export const streamLogsDocker = async (
  ipAddress: string, 
  onLogReceived: (log: string) => void,
  abortController: AbortController
): Promise<void> => {
  let accumulatedData = '';

  try {
    await api.get('/stream_logs', {
      params: { ip_address: ipAddress },
      responseType: 'text',
      signal: abortController.signal,
      onDownloadProgress: (progressEvent: any) => {
        if (progressEvent.event?.target instanceof XMLHttpRequest) {
          const newData = progressEvent.event.target.responseText;
          const newContent = newData.substring(accumulatedData.length);
          accumulatedData = newData;
          
          const lines = newContent.split('\n');
          lines.forEach((line: string) => {
            if (line.trim()) {
              if (line.startsWith('data: ')) {
                const logContent = line.slice(6); // Removes 'data: ' prefix
                onLogReceived(logContent);
              } else {
                onLogReceived(line.trim());
              }
            }
          });
        }
      },
    });
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Fetch aborted');
    } else {
      console.error('Error streaming logs:', error);
      throw error;
    }
  }
};

export const getInstanceStatus = async (instanceIds: string[]) => {
  const params = new URLSearchParams();
  instanceIds.forEach(id => params.append('instance_ids[]', id));
  const response = await api.get('/instance_status', { params: { params} });
  return response.data;
};
