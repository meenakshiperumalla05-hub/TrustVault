import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import {
  ShieldCheck, LockKeyhole, FileText, Upload, Search, Download,
  Share2, Trash2, Pencil, LogOut, Users, Activity, Plus,
  RefreshCw, X, FolderLock
} from "lucide-react";

const API = "http://127.0.0.1:8001";

const api = axios.create({ baseURL: API });
const getErrorMessage = (err: any, fallback: string): string => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item: any) =>
      typeof item === "string" ? item : item?.msg || JSON.stringify(item)
    ).join("; ");
  }
  if (detail && typeof detail === "object") return detail.message || JSON.stringify(detail);
  return err?.message || fallback;
};


api.interceptors.request.use((config) => {
  const token = localStorage.getItem("trustvault_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

type DocumentItem = {
  id: number;
  name: string;
  description?: string;
  category?: string;
  owner_id?: number;
  file_size?: number;
  content_type?: string;
  created_at?: string;
};

type User = {
  id: number;
  full_name: string;
  email: string;
  role: string;
};

const styles = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;font-family:'DM Sans',sans-serif;background:#f5f7fb;color:#172033}
button,input,textarea,select{font:inherit}
button{cursor:pointer}
.auth-page{min-height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#101d39,#253e70);padding:24px}
.auth-card{background:white;width:min(430px,100%);padding:38px;border-radius:22px;box-shadow:0 24px 80px #0003}
.brand-mark{background:#e9edff;color:#4658cf;width:62px;height:62px;border-radius:18px;display:grid;place-items:center;margin-bottom:18px}
.auth-card h1{font:800 30px Manrope;margin:0}
.muted{color:#8a93a6;font-size:13px}
.auth-tabs{display:flex;background:#f1f3f8;border-radius:10px;padding:4px;margin:25px 0}
.auth-tabs button{border:0;background:transparent;padding:10px;flex:1;border-radius:8px;color:#68738a}
.auth-tabs .selected{background:white;color:#3447bd;box-shadow:0 1px 5px #0001;font-weight:700}
label{display:block;font-size:13px;font-weight:700;color:#39445b;margin:15px 0}
input,textarea,select{display:block;width:100%;padding:12px 13px;border:1px solid #dce1eb;border-radius:9px;margin-top:7px;outline:none;background:white;color:#202b40}
input:focus,textarea:focus,select:focus{border-color:#6878e6;box-shadow:0 0 0 3px #6878e61c}
textarea{min-height:85px;resize:vertical}
.primary{border:0;background:#4e5fd0;color:white;padding:12px 17px;border-radius:9px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:8px}
.primary:hover{background:#394bb9}
.primary:disabled{opacity:.6}
.full{width:100%;margin-top:12px}
.auth-footer{display:flex;justify-content:center;align-items:center;gap:7px;color:#8791a5;font-size:11px;margin-top:24px}
.app-shell{min-height:100vh;display:flex}
.sidebar{width:245px;background:#111d38;color:white;padding:27px 17px;display:flex;flex-direction:column;flex-shrink:0}
.brand{font:800 21px Manrope;display:flex;align-items:center;gap:11px;padding:0 12px 38px;color:#fff}
.brand svg{color:#8795ff}
.side-label,.eyebrow{font-size:10px;font-weight:800;letter-spacing:1.5px;color:#8c98b5}
.side-label{padding:0 12px 12px}
.nav{border:0;background:transparent;color:#aeb8ce;display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:9px;text-align:left;margin-bottom:5px;font-size:13px}
.nav.active,.nav:hover{background:#27365b;color:white}
.sidebar-bottom{margin-top:auto}
.user-card{display:flex;align-items:center;gap:10px;padding:15px 9px;border-top:1px solid #ffffff18}
.avatar{width:36px;height:36px;border-radius:50%;background:#5868cf;display:grid;place-items:center;font-weight:800}
.user-info{display:flex;flex-direction:column;gap:3px;min-width:0}
.user-info strong{font-size:12px}
.user-info small{color:#9ba8c3;text-transform:capitalize}
.logout{width:100%}
.main{padding:32px 42px;max-width:1500px;width:100%;margin:0 auto}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:27px}
.topbar h2{font:800 27px Manrope;margin:5px 0}
.top-actions{display:flex;gap:12px;align-items:center}
.secure-pill{font-size:12px;color:#368365;background:#e5f5ed;padding:9px 12px;border-radius:20px;display:flex;gap:6px;align-items:center}
.icon-button{border:1px solid #e0e5ee;background:white;color:#58647a;border-radius:9px;padding:9px;display:grid;place-items:center}
.welcome{background:linear-gradient(110deg,#293b76,#5968d4);border-radius:16px;padding:26px 30px;color:white;display:flex;justify-content:space-between;align-items:center}
.welcome h3{font:700 20px Manrope;margin:0 0 8px}
.welcome p{font-size:13px;color:#d9dfff;margin:0}
.welcome-icon{width:70px;height:70px;border-radius:20px;background:#ffffff20;display:grid;place-items:center}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:17px;margin:22px 0}
.stat-card{background:white;border:1px solid #e9edf4;border-radius:13px;padding:18px;display:flex;align-items:center;gap:14px}
.stat-icon{width:42px;height:42px;border-radius:12px;display:grid;place-items:center}
.stat-icon svg{width:20px}
.purple{background:#efedff;color:#6457c9}
.green{background:#e7f7ef;color:#26956a}
.blue{background:#e9f3ff;color:#3982c9}
.stat-card small{display:block;color:#8791a5;font-size:11px;margin-bottom:5px}
.stat-card strong{font:700 18px Manrope;text-transform:capitalize}
.toolbar{display:flex;justify-content:space-between;gap:14px;margin:25px 0}
.search-box{display:flex;align-items:center;gap:10px;background:white;border:1px solid #e4e8f0;border-radius:9px;padding:0 12px;width:min(380px,100%);color:#8b95a8}
.search-box input{border:0;margin:0;box-shadow:none!important}
.document-section{background:white;border:1px solid #e8ecf3;border-radius:14px;padding:24px}
.section-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.section-heading h3{font:700 17px Manrope;margin:0 0 5px}
.section-heading p{font-size:12px;color:#929bad;margin:0}
.count{background:#f0f2fa;color:#5b68bb;border-radius:20px;padding:7px 11px;font-size:11px;font-weight:700}
.document-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(245px,1fr));gap:15px}
.doc-card{border:1px solid #e9edf3;border-radius:12px;padding:17px;transition:.2s}
.doc-card:hover{border-color:#bfc8f3;box-shadow:0 7px 22px #1b2b5010}
.doc-top{display:flex;justify-content:space-between;align-items:center}
.file-icon{width:42px;height:42px;background:#eff1ff;color:#5b66c9;border-radius:11px;display:grid;place-items:center}
.category{font-size:10px;background:#f1f3f8;padding:6px 9px;border-radius:20px;color:#69758c}
.doc-card h3{font:700 14px Manrope;margin:17px 0 7px;overflow-wrap:anywhere}
.doc-description{font-size:12px;color:#8791a5;min-height:32px}
.doc-meta{display:flex;justify-content:space-between;color:#9ba4b4;font-size:10px;border-top:1px solid #edf0f5;padding-top:12px;margin-top:15px}
.doc-actions{display:flex;gap:7px;margin-top:14px}
.doc-actions button{flex:1;border:1px solid #e8ebf2;background:white;color:#67738b;border-radius:7px;padding:8px;display:grid;place-items:center}
.doc-actions button:hover{background:#f0f2ff;color:#4e5fd0}
.doc-actions .danger-icon:hover{background:#fff0f0;color:#d54b4b}
.empty{text-align:center;padding:55px 15px;color:#a0a9b8}
.empty h3{color:#4d5870;font-size:15px}
.empty p{font-size:12px}
.modal-backdrop{position:fixed;inset:0;background:#101a32a6;display:grid;place-items:center;padding:18px;z-index:5;overflow:auto}
.modal{background:white;width:min(480px,100%);max-height:90vh;overflow:auto;border-radius:16px;padding:25px;box-shadow:0 20px 70px #0003}
.modal-heading{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}
.modal-heading h3{font:700 19px Manrope;margin:0 0 5px}
.modal-heading p{font-size:12px;color:#929bad;margin:0}
.alert{padding:12px 14px;border-radius:9px;font-size:12px;margin:12px 0;display:flex;justify-content:space-between;gap:10px}
.alert button{border:0;background:transparent}
.error{background:#fff0f0;color:#bd3c3c}
.success{background:#eaf8f0;color:#238257}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:12px;text-align:left}
th{color:#8993a6;font-size:10px;text-transform:uppercase;letter-spacing:.7px;background:#f8f9fc}
td,th{padding:14px;border-bottom:1px solid #edf0f5;white-space:nowrap}
.status{background:#e9f6ee;color:#26835b;padding:5px 8px;border-radius:15px;font-size:10px}
.permission-list{border-top:1px solid #edf0f5;margin-top:22px;padding-top:14px}
.permission-list h4{font-size:13px}
.permission-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f0f2f6;font-size:12px}
.danger-text{border:0;background:transparent;color:#d44d4d;font-weight:700}
@media(max-width:760px){
.sidebar{width:65px;padding:20px 7px}
.brand span,.side-label{display:none}
.brand{padding:0 9px 35px}
.brand svg{width:28px}
.nav{justify-content:center;padding:13px 5px;font-size:0}
.nav svg{width:20px;height:20px}
.user-info{display:none}
.user-card{justify-content:center}
.main{padding:22px 14px}
.stats{grid-template-columns:1fr}
.welcome{padding:20px}
.welcome-icon{display:none}
.topbar h2{font-size:22px}
.toolbar{flex-wrap:wrap}
.search-box{width:100%}
.document-section{padding:16px}
}
`;

function StyleSheet() {
  return <style>{styles}</style>;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("documents");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  const [showUpload, setShowUpload] = useState(false);
  const [showShare, setShowShare] = useState<number | null>(null);
  const [showEdit, setShowEdit] = useState<DocumentItem | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [docName, setDocName] = useState("");
  const [category, setCategory] = useState("General");
  const [description, setDescription] = useState("");
  const [shareUserEmail, setShareUserEmail] = useState("");
  const [sharePermission, setSharePermission] = useState("read");
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);

  useEffect(() => {
    if (localStorage.getItem("trustvault_token")) loadProfile();
  }, []);

  async function loadProfile() {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch {
      localStorage.removeItem("trustvault_token");
      setUser(null);
    }
  }

  async function loadDocuments() {
    try {
      const response = await api.get("/documents", {
        params: search ? { search } : {}
      });
      const data = response.data;
      setDocuments(Array.isArray(data) ? data : data.items || data.documents || []);
    } catch (err: any) {
      setError(getErrorMessage(err, "Unable to load documents."));
    }
  }

  useEffect(() => {
    if (user) loadDocuments();
  }, [user, search]);

  async function authenticate(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (authMode === "register") {
        await api.post("/auth/register", {
          full_name: fullName,
          email,
          password
        });
      }

      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);

      const response = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });

      localStorage.setItem("trustvault_token", response.data.access_token);
      await loadProfile();
    } catch (err: any) {
      setError(getErrorMessage(err, "Authentication failed."));
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("trustvault_token");
    setUser(null);
    setDocuments([]);
    setTab("documents");
  }

  async function uploadDocument(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please select a file.");
      return;
    }

    const form = new FormData();
    form.append("file", file);
    form.append("name", docName || file.name);
    form.append("description", description);
    form.append("category", category);

    try {
      await api.post("/documents/upload", form);
      setShowUpload(false);
      setFile(null);
      setDocName("");
      setDescription("");
      setMessage("Document uploaded successfully.");
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, "Upload failed."));
    }
  }

  async function downloadDocument(doc: DocumentItem) {
    try {
      const response = await api.get(`/documents/${doc.id}/download`, {
        responseType: "blob"
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = doc.name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(getErrorMessage(err, "Download failed."));
    }
  }

  async function deleteDocument(id: number) {
    if (!window.confirm("Are you sure you want to delete this document?")) return;
    try {
      await api.delete(`/documents/${id}`);
      setMessage("Document deleted.");
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, "Delete failed."));
    }
  }

  async function updateDocument(e: FormEvent) {
    e.preventDefault();
    if (!showEdit) return;

    try {
      await api.put(`/documents/${showEdit.id}`, {
        name: docName,
        description,
        category
      });
      setShowEdit(null);
      setMessage("Document details updated.");
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, "Update failed."));
    }
  }

  async function shareDocument(e: FormEvent) {
    e.preventDefault();
    if (!showShare) return;

    try {
      await api.post(`/documents/${showShare}/share`, {
        user_email: shareUserEmail.trim().toLowerCase(),
        permission: sharePermission
      });
      setShareUserEmail("");
      setMessage("Document access granted.");
      await loadPermissions(showShare);
    } catch (err: any) {
      setError(getErrorMessage(err, "Sharing failed."));
    }
  }

  async function loadPermissions(id: number) {
    try {
      const response = await api.get(`/documents/${id}/permissions`);
      const data = response.data;
      setPermissions(Array.isArray(data) ? data : data.items || []);
      setShowShare(id);
    } catch (err: any) {
      setError(getErrorMessage(err, "Unable to load permissions."));
    }
  }

  async function revokePermission(docId: number, userId: number) {
    try {
      await api.delete(`/documents/${docId}/share/${userId}`);
      setMessage("Access revoked.");
      await loadPermissions(docId);
    } catch (err: any) {
      setError(getErrorMessage(err, "Unable to revoke access."));
    }
  }

  async function loadAuditLogs() {
    try {
      const response = await api.get("/admin/audit-logs");
      const data = response.data;
      setAuditLogs(Array.isArray(data) ? data : data.items || []);
    } catch (err: any) {
      setError(getErrorMessage(err, "Unable to load audit logs."));
    }
  }

  useEffect(() => {
    if (user && tab === "audit") loadAuditLogs();
  }, [tab, user]);

  function openEdit(doc: DocumentItem) {
    setDocName(doc.name);
    setDescription(doc.description || "");
    setCategory(doc.category || "General");
    setShowEdit(doc);
  }

  if (!user) {
    return (
      <>
        <StyleSheet />
        <div className="auth-page">
          <div className="auth-card">
            <div className="brand-mark"><ShieldCheck size={34} /></div>
            <h1>TrustVault</h1>
            <p className="muted">Secure document sharing. Complete control.</p>

            <div className="auth-tabs">
              <button className={authMode === "login" ? "selected" : ""}
                onClick={() => setAuthMode("login")}>Login</button>
              <button className={authMode === "register" ? "selected" : ""}
                onClick={() => setAuthMode("register")}>Create account</button>
            </div>

            <form onSubmit={authenticate}>
              {authMode === "register" && (
                <label>Full name
                  <input required value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="Your name" />
                </label>
              )}

              <label>Email address
                <input type="email" required value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com" />
              </label>

              <label>Password
                <input type="password" required minLength={8} value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password" />
              </label>

              {error && <div className="alert error">{error}</div>}

              <button className="primary full" disabled={loading}>
                {loading ? "Please wait..." :
                  authMode === "login" ? "Sign in" : "Create account"}
              </button>
            </form>

            <div className="auth-footer">
              <LockKeyhole size={14} /> Protected by TrustVault access controls
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <StyleSheet />
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand">
            <ShieldCheck size={29} />
            <span>TrustVault</span>
          </div>

          <div className="side-label">WORKSPACE</div>
          <button className={tab === "documents" ? "nav active" : "nav"}
            onClick={() => setTab("documents")}>
            <FolderLock size={18} /> My documents
          </button>

          {user.role === "admin" && (
            <button className={tab === "audit" ? "nav active" : "nav"}
              onClick={() => setTab("audit")}>
              <Activity size={18} /> Audit activity
            </button>
          )}

          <div className="sidebar-bottom">
            <div className="user-card">
              <div className="avatar">{user.full_name?.[0]?.toUpperCase() || "U"}</div>
              <div className="user-info">
                <strong>{user.full_name}</strong>
                <small>{user.role}</small>
              </div>
            </div>
            <button className="nav logout" onClick={logout}>
              <LogOut size={18} /> Sign out
            </button>
          </div>
        </aside>

        <main className="main">
          <header className="topbar">
            <div>
              <span className="eyebrow">SECURE WORKSPACE</span>
              <h2>{tab === "audit" ? "Audit activity" : "Documents"}</h2>
            </div>
            <div className="top-actions">
              <span className="secure-pill"><LockKeyhole size={14} /> Secure session</span>
              <button className="icon-button" onClick={() =>
                tab === "audit" ? loadAuditLogs() : loadDocuments()}>
                <RefreshCw size={17} />
              </button>
            </div>
          </header>

          {error && <div className="alert error">{error}
            <button onClick={() => setError("")}><X size={15} /></button>
          </div>}
          {message && <div className="alert success">{message}
            <button onClick={() => setMessage("")}><X size={15} /></button>
          </div>}

          {tab === "documents" && (
            <>
              <section className="welcome">
                <div>
                  <h3>Your files, under your control.</h3>
                  <p>Manage documents and control who can access them.</p>
                </div>
                <div className="welcome-icon"><ShieldCheck size={42} /></div>
              </section>

              <section className="stats">
                <div className="stat-card">
                  <div className="stat-icon purple"><FileText /></div>
                  <div><small>Visible documents</small><strong>{documents.length}</strong></div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon green"><LockKeyhole /></div>
                  <div><small>Access controlled</small><strong>Protected</strong></div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon blue"><Users /></div>
                  <div><small>Your role</small><strong>{user.role}</strong></div>
                </div>
              </section>

              <section className="toolbar">
                <div className="search-box">
                  <Search size={18} />
                  <input value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Search documents..." />
                </div>
                {(user.role === "owner" || user.role === "admin") && (
                  <button className="primary" onClick={() => setShowUpload(true)}>
                    <Plus size={18} /> Upload document
                  </button>
                )}
              </section>

              <section className="document-section">
                <div className="section-heading">
                  <div><h3>All documents</h3>
                    <p>Your accessible documents and shared files</p></div>
                  <span className="count">{documents.length} files</span>
                </div>

                {documents.length === 0 ? (
                  <div className="empty">
                    <FileText size={42} />
                    <h3>No documents found</h3>
                    <p>Upload a document or try another search.</p>
                  </div>
                ) : (
                  <div className="document-grid">
                    {documents.map(doc => (
                      <article className="doc-card" key={doc.id}>
                        <div className="doc-top">
                          <div className="file-icon"><FileText size={23} /></div>
                          <span className="category">{doc.category || "General"}</span>
                        </div>
                        <h3>{doc.name}</h3>
                        <p className="doc-description">{doc.description || "No description provided."}</p>
                        <div className="doc-meta">
                          <span>Document #{doc.id}</span>
                          {doc.created_at && <span>{new Date(doc.created_at).toLocaleDateString()}</span>}
                        </div>
                        <div className="doc-actions">
                          <button title="Download" onClick={() => downloadDocument(doc)}>
                            <Download size={16} />
                          </button>
                          <button title="Share and permissions" onClick={() => loadPermissions(doc.id)}>
                            <Share2 size={16} />
                          </button>
                          <button title="Edit details" onClick={() => openEdit(doc)}>
                            <Pencil size={16} />
                          </button>
                          <button title="Delete" className="danger-icon"
                            onClick={() => deleteDocument(doc.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}

          {tab === "audit" && user.role === "admin" && (
            <section className="document-section">
              <div className="section-heading">
                <div><h3>System audit trail</h3>
                  <p>Recorded document and access activity</p></div>
                <span className="count">{auditLogs.length} events</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>Action</th><th>Actor ID</th><th>Document ID</th>
                    <th>Status</th><th>Date</th>
                  </tr></thead>
                  <tbody>
                    {auditLogs.map((log, index) => (
                      <tr key={log.id || index}>
                        <td><strong>{log.action}</strong></td>
                        <td>{log.actor_id ?? "System"}</td>
                        <td>{log.document_id ?? log.metadata_json?.deleted_document_id ?? "—"}</td>
                        <td><span className="status">{log.status || "Recorded"}</span></td>
                        <td>{log.created_at ? new Date(log.created_at).toLocaleString() : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {auditLogs.length === 0 && <div className="empty">No audit events found.</div>}
              </div>
            </section>
          )}
        </main>

        {showUpload && (
          <div className="modal-backdrop">
            <form className="modal" onSubmit={uploadDocument}>
              <div className="modal-heading"><div><h3>Upload document</h3>
                <p>Add a file to your secure workspace.</p></div>
                <button type="button" className="icon-button" onClick={() => setShowUpload(false)}><X /></button>
              </div>
              <label>Choose file
                <input type="file" required accept=".pdf,.docx,.xlsx,.txt,.png,.jpg,.jpeg"
                  onChange={e => setFile(e.target.files?.[0] || null)} />
              </label>
              <label>Document name
                <input value={docName} onChange={e => setDocName(e.target.value)}
                  placeholder="Document name" />
              </label>
              <label>Category
                <input value={category} onChange={e => setCategory(e.target.value)} required />
              </label>
              <label>Description
                <textarea value={description} onChange={e => setDescription(e.target.value)}
                  placeholder="Add a short description" />
              </label>
              <button className="primary full"><Upload size={17} /> Upload securely</button>
            </form>
          </div>
        )}

        {showEdit && (
          <div className="modal-backdrop">
            <form className="modal" onSubmit={updateDocument}>
              <div className="modal-heading"><div><h3>Edit document</h3>
                <p>Update document information.</p></div>
                <button type="button" className="icon-button" onClick={() => setShowEdit(null)}><X /></button>
              </div>
              <label>Name<input required value={docName}
                onChange={e => setDocName(e.target.value)} /></label>
              <label>Category<input required value={category}
                onChange={e => setCategory(e.target.value)} /></label>
              <label>Description<textarea value={description}
                onChange={e => setDescription(e.target.value)} /></label>
              <button className="primary full">Save changes</button>
            </form>
          </div>
        )}

        {showShare !== null && (
          <div className="modal-backdrop">
            <div className="modal">
              <div className="modal-heading"><div><h3>Access management</h3>
                <p>Grant or revoke document access.</p></div>
                <button className="icon-button" onClick={() => setShowShare(null)}><X /></button>
              </div>
              <form onSubmit={shareDocument}>
                <label>Recipient email address
                  <input type="email" required value={shareUserEmail}
                    onChange={e => setShareUserEmail(e.target.value)}
                    placeholder="Enter registered user email" />
                </label>
                <label>Permission level
                  <select value={sharePermission}
                    onChange={e => setSharePermission(e.target.value)}>
                    <option value="read">Read only</option>
                    <option value="edit">Read and edit</option>
                  </select>
                </label>
                <button className="primary full"><Share2 size={16} /> Grant access</button>
              </form>
              <div className="permission-list">
                <h4>Existing permissions</h4>
                {permissions.map((p, index) => (
                  <div className="permission-row" key={p.id || index}>
                    <span>User #{p.user_id} · {p.permission}</span>
                    <button className="danger-text"
                      onClick={() => revokePermission(showShare, p.user_id)}>
                      Revoke
                    </button>
                  </div>
                ))}
                {permissions.length === 0 && <p className="muted">No shared permissions returned.</p>}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}