import apiAxios from "../intersptors/Mainintersptors";

// Organization
export const getOrganizations = () => apiAxios.get("organizations/");
export const createOrganization = (data) => apiAxios.post("organizations/", data);

// Membership
export const getMembers = (orgId) => apiAxios.get(`organizations/${orgId}/members/`);
export const inviteMember = (orgId, data) => apiAxios.post(`organizations/${orgId}/members/`, data);

// Invites
export const getInvites = () => apiAxios.get("invites/");
export const acceptInvite = (token) => apiAxios.post(`invites/${token}/`);