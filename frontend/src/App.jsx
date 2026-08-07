import { useEffect, useMemo, useState } from 'react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

const pageDefinitions = [
  { id: 'login', label: 'Login' },
  { id: 'products', label: 'Products' },
  { id: 'orders', label: 'Orders' },
  { id: 'security', label: 'Security' },
  { id: 'system', label: 'System' }
];

const storageKeys = {
  token: 'demoshop-token',
  user: 'demoshop-user'
};

const initialLoginForm = {
  username: 'admin',
  password: 'admin123'
};

const initialProductForm = {
  id: '',
  name: '',
  description: '',
  price: '',
  stock: ''
};

const initialOrderForm = {
  productId: '',
  quantity: '1'
};

function App() {
  const [activePage, setActivePage] = useState(() => getPageFromHash());
  const [token, setToken] = useState(() => localStorage.getItem(storageKeys.token) ?? '');
  const [user, setUser] = useState(() => readJsonStorage(storageKeys.user));
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loginForm, setLoginForm] = useState(initialLoginForm);
  const [productForm, setProductForm] = useState(initialProductForm);
  const [orderForm, setOrderForm] = useState(initialOrderForm);
  const [loading, setLoading] = useState({ login: false, products: false, orders: false });

  useEffect(() => {
    const handleHashChange = () => setActivePage(getPageFromHash());

    window.addEventListener('hashchange', handleHashChange);

    if (!window.location.hash) {
      window.location.hash = '#/login';
    }

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    void refreshProducts();
    void refreshOrders();
  }, []);

  useEffect(() => {
    if (products.length > 0 && !orderForm.productId) {
      setOrderForm((current) => ({
        ...current,
        productId: String(products[0].id)
      }));
    }
  }, [products, orderForm.productId]);

  const currentUserLabel = useMemo(() => {
    if (!user) {
      return 'Not logged in';
    }

    return `${user.username} (${user.role})`;
  }, [user]);

  function addNotification(kind, title, message) {
    const notificationId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    setNotifications((current) => [
      {
        id: notificationId,
        kind,
        title,
        message
      },
      ...current
    ].slice(0, 4));

    window.setTimeout(() => {
      setNotifications((current) => current.filter((item) => item.id !== notificationId));
    }, 3500);
  }

  function addActivity(eventName, detail, state = 'info') {
    const activityId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    setActivity((current) => [
      {
        id: activityId,
        eventName,
        detail,
        state,
        timestamp: new Date().toLocaleTimeString()
      },
      ...current
    ].slice(0, 8));
  }

  async function apiRequest(path, options = {}) {
    const { method = 'GET', body, token: authToken = token } = options;
    const headers = {
      Accept: 'application/json'
    };

    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    });

    let payload = {};

    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    if (!response.ok) {
      throw new Error(payload.message || payload.error || `Request failed with status ${response.status}`);
    }

    return payload;
  }

  async function refreshProducts() {
    setLoading((current) => ({ ...current, products: true }));

    try {
      const payload = await apiRequest('/products', { token: '' });
      setProducts(payload.products ?? []);
    } catch (error) {
      addNotification('error', 'Products unavailable', error.message);
    } finally {
      setLoading((current) => ({ ...current, products: false }));
    }
  }

  async function refreshOrders() {
    setLoading((current) => ({ ...current, orders: true }));

    try {
      const payload = await apiRequest('/orders', { token: '' });
      setOrders(payload.orders ?? []);
    } catch (error) {
      addNotification('error', 'Orders unavailable', error.message);
    } finally {
      setLoading((current) => ({ ...current, orders: false }));
    }
  }

  async function handleLoginSubmit(event) {
    event.preventDefault();
    setLoading((current) => ({ ...current, login: true }));

    try {
      const payload = await apiRequest('/login', {
        method: 'POST',
        body: loginForm,
        token: ''
      });

      setToken(payload.token);
      setUser(payload.user);
      localStorage.setItem(storageKeys.token, payload.token);
      localStorage.setItem(storageKeys.user, JSON.stringify(payload.user));

      addActivity('USER_LOGIN_SUCCESS', `Logged in as ${payload.user.username}`, 'success');
      addNotification('success', 'Login successful', payload.message || 'Login succeeded');
      void refreshProfile(payload.token);
    } catch (error) {
      addActivity('USER_LOGIN_FAILED', error.message, 'error');
      addNotification('error', 'Login failed', error.message);
    } finally {
      setLoading((current) => ({ ...current, login: false }));
    }
  }

  async function refreshProfile(activeToken) {
    try {
      const payload = await apiRequest('/profile', { token: activeToken });
      addActivity('HTTP_RESPONSE', `Profile loaded for ${payload.user.username}`, 'info');
    } catch (error) {
      addNotification('error', 'Profile check failed', error.message);
    }
  }

  async function handleCreateProduct() {
    try {
      const payload = await apiRequest('/products', {
        method: 'POST',
        body: {
          name: productForm.name,
          description: productForm.description,
          price: Number(productForm.price),
          stock: Number(productForm.stock || 0)
        }
      });

      addActivity('PRODUCT_CREATED', `Created product #${payload.product.id}`, 'success');
      addNotification('success', 'Product created', payload.message || 'Product added successfully');
      setProductForm(initialProductForm);
      await refreshProducts();
    } catch (error) {
      addNotification('error', 'Create product failed', error.message);
      addActivity('HTTP_RESPONSE', error.message, 'error');
    }
  }

  async function handleUpdateProduct() {
    const productId = Number(productForm.id);

    if (!productId) {
      addNotification('error', 'Update product failed', 'Enter a product ID first.');
      return;
    }

    try {
      const payload = await apiRequest(`/products/${productId}`, {
        method: 'PUT',
        body: {
          name: productForm.name || undefined,
          description: productForm.description || undefined,
          price: productForm.price === '' ? undefined : Number(productForm.price),
          stock: productForm.stock === '' ? undefined : Number(productForm.stock)
        }
      });

      addActivity('PRODUCT_UPDATED', `Updated product #${payload.product.id}`, 'success');
      addNotification('success', 'Product updated', payload.message || 'Product updated successfully');
      await refreshProducts();
    } catch (error) {
      addNotification('error', 'Update product failed', error.message);
      addActivity('HTTP_RESPONSE', error.message, 'error');
    }
  }

  async function handleDeleteProduct() {
    const productId = Number(productForm.id);

    if (!productId) {
      addNotification('error', 'Delete product failed', 'Enter a product ID first.');
      return;
    }

    try {
      await apiRequest(`/products/${productId}`, { method: 'DELETE' });
      addActivity('PRODUCT_DELETED', `Deleted product #${productId}`, 'success');
      addNotification('success', 'Product deleted', `Product ${productId} removed successfully.`);
      setProductForm(initialProductForm);
      await refreshProducts();
    } catch (error) {
      addNotification('error', 'Delete product failed', error.message);
      addActivity('HTTP_RESPONSE', error.message, 'error');
    }
  }

  async function handlePlaceOrder() {
    const productId = Number(orderForm.productId);
    const quantity = Number(orderForm.quantity);

    if (!productId || !quantity) {
      addNotification('error', 'Place order failed', 'Choose a product and quantity first.');
      return;
    }

    try {
      const payload = await apiRequest('/orders', {
        method: 'POST',
        body: {
          product_id: productId,
          quantity
        }
      });

      addActivity('ORDER_PLACED', `Order #${payload.order.id} placed`, 'success');
      addNotification('success', 'Order placed', payload.message || 'Order placed successfully');
      await refreshOrders();
      await refreshProducts();
    } catch (error) {
      addActivity('ORDER_FAILED', error.message, 'error');
      addNotification('error', 'Order failed', error.message);
    }
  }

  async function handleCancelOrder() {
    const latestOrder = orders[0];

    if (!latestOrder) {
      addNotification('error', 'Cancel order failed', 'No existing order is available to test the failure path.');
      return;
    }

    try {
      await apiRequest('/orders', {
        method: 'POST',
        body: {
          product_id: latestOrder.product_id,
          quantity: 0
        }
      });
    } catch (error) {
      addActivity('ORDER_FAILED', `Cancel flow triggered for order #${latestOrder.id}`, 'warning');
      addNotification(
        'warning',
        'Cancel flow triggered',
        'DemoShop does not expose a cancel-order endpoint, so this uses the existing invalid-order path.'
      );
    }
  }

  async function triggerUnauthorizedAccess() {
    try {
      await apiRequest('/profile', { token: '' });
    } catch (error) {
      addActivity('UNAUTHORIZED_ACCESS', error.message, 'warning');
      addNotification('warning', 'Unauthorized access logged', 'The protected profile route rejected the request.');
    }
  }

  async function checkSystemHealth() {
    try {
      const payload = await apiRequest('/health', { token: '' });
      addActivity('HTTP_RESPONSE', payload.status || 'healthy', 'success');
      addNotification('success', 'Application healthy', 'The backend health route responded successfully.');
    } catch (error) {
      addNotification('error', 'Health check failed', error.message);
      addActivity('APPLICATION_ERROR', error.message, 'error');
    }
  }

  async function triggerSystemError() {
    try {
      await apiRequest('/test-error', { token: '' });
    } catch (error) {
      addActivity('APPLICATION_ERROR', error.message, 'error');
      addNotification('error', 'System error captured', 'The test-error route intentionally throws the backend error flow.');
    }
  }

  function useProductInForm(product) {
    setProductForm({
      id: String(product.id),
      name: product.name,
      description: product.description,
      price: String(product.price),
      stock: String(product.stock)
    });
  }

  function useProductForOrder(product) {
    setOrderForm({
      productId: String(product.id),
      quantity: '1'
    });
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-main">
          <p className="eyebrow">DemoShop x LogSherlock</p>
          <h1>Shop, test, and watch every event unfold.</h1>
          <p className="hero-copy">
            This storefront keeps the existing Flask routes and log events intact while presenting the same flows in a calmer, more realistic ecommerce experience.
          </p>

          <div className="hero-actions">
            <a className="primary-button hero-link" href="#/products">
              Browse products
            </a>
            <a className="secondary-button hero-link" href="#/orders">
              Place an order
            </a>
          </div>
        </div>

        <div className="hero-panel">
          <div className="hero-panel-row">
            <span className="hero-panel-label">Session</span>
            <strong>{currentUserLabel}</strong>
          </div>
          <div className="hero-panel-row">
            <span className="hero-panel-label">Inventory</span>
            <strong>{products.length} active products</strong>
          </div>
          <div className="hero-panel-row">
            <span className="hero-panel-label">Orders</span>
            <strong>{orders.length} recent orders</strong>
          </div>
        </div>
      </header>

      <nav className="page-nav" aria-label="DemoShop pages">
        {pageDefinitions.map((page) => (
          <a
            key={page.id}
            href={`#/${page.id}`}
            className={activePage === page.id ? 'nav-link active' : 'nav-link'}
          >
            {page.label}
          </a>
        ))}
      </nav>

      <section className="notification-stack" aria-live="polite" aria-atomic="true">
        {notifications.map((notification) => (
          <article key={notification.id} className={`notification ${notification.kind}`}>
            <strong>{notification.title}</strong>
            <p>{notification.message}</p>
          </article>
        ))}
      </section>

      <main className="workspace">
        <section className="primary-column">
          {activePage === 'login' && (
            <>
              <PageCard
                title="Welcome back"
                description="Authenticate with the existing login route and let the activity feed document the result."
                actions={
                  <button className="secondary-button" type="button" onClick={() => void refreshProfile(token)}>
                    Check profile
                  </button>
                }
              >
                <form className="form-grid" onSubmit={handleLoginSubmit}>
                  <Field label="Username">
                    <input
                      value={loginForm.username}
                      onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })}
                      placeholder="admin"
                    />
                  </Field>

                  <Field label="Password">
                    <input
                      type="password"
                      value={loginForm.password}
                      onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                      placeholder="admin123"
                    />
                  </Field>

                  <div className="action-row full-span">
                    <button className="primary-button" type="submit" disabled={loading.login}>
                      {loading.login ? 'Logging in...' : 'Login'}
                    </button>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => setLoginForm(initialLoginForm)}
                    >
                      Reset
                    </button>
                  </div>
                </form>
              </PageCard>

              <div className="feature-grid">
                <article className="feature-card">
                  <p className="eyebrow">Quick start</p>
                  <h3>Use the seeded admin account</h3>
                  <p>Username admin and password admin123 still trigger the same backend login flow.</p>
                </article>
                <article className="feature-card">
                  <p className="eyebrow">Protected flow</p>
                  <h3>Profile checks remain secured by the token guard</h3>
                  <p>The same bearer-token route powers the experience, now framed as a secure checkout journey.</p>
                </article>
              </div>
            </>
          )}

          {activePage === 'products' && (
            <>
              <PageCard
                title="Catalog manager"
                description="Create, update, and review products in a cleaner storefront layout while keeping the backend API unchanged."
                actions={
                  <button className="secondary-button" type="button" onClick={() => void refreshProducts()}>
                    Refresh products
                  </button>
                }
              >
                <div className="mini-stats">
                  <div className="mini-stat">
                    <span>Featured</span>
                    <strong>{products[0] ? products[0].name : 'No item yet'}</strong>
                  </div>
                  <div className="mini-stat">
                    <span>Stock focus</span>
                    <strong>{products.reduce((sum, product) => sum + Number(product.stock || 0), 0)} units</strong>
                  </div>
                </div>

                <form className="form-grid">
                  <Field label="Product ID">
                    <input
                      value={productForm.id}
                      onChange={(event) => setProductForm({ ...productForm, id: event.target.value })}
                      placeholder="1"
                    />
                  </Field>

                  <Field label="Name">
                    <input
                      value={productForm.name}
                      onChange={(event) => setProductForm({ ...productForm, name: event.target.value })}
                      placeholder="Demo Product"
                    />
                  </Field>

                  <Field label="Description" className="full-span">
                    <textarea
                      rows={4}
                      value={productForm.description}
                      onChange={(event) => setProductForm({ ...productForm, description: event.target.value })}
                      placeholder="Short description of the product"
                    />
                  </Field>

                  <Field label="Price">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={productForm.price}
                      onChange={(event) => setProductForm({ ...productForm, price: event.target.value })}
                      placeholder="19.99"
                    />
                  </Field>

                  <Field label="Stock">
                    <input
                      type="number"
                      min="0"
                      value={productForm.stock}
                      onChange={(event) => setProductForm({ ...productForm, stock: event.target.value })}
                      placeholder="10"
                    />
                  </Field>

                  <div className="action-row full-span">
                    <button className="primary-button" type="button" onClick={() => void handleCreateProduct()}>
                      Create product
                    </button>
                    <button className="secondary-button" type="button" onClick={() => void handleUpdateProduct()}>
                      Update product
                    </button>
                    <button className="danger-button" type="button" onClick={() => void handleDeleteProduct()}>
                      Delete product
                    </button>
                  </div>
                </form>
              </PageCard>

              <div className="subsection">
                <div className="subsection-heading">
                  <h3>Trending items</h3>
                  <span>{loading.products ? 'Loading...' : `${products.length} items available`}</span>
                </div>

                <div className="product-grid">
                  {products.map((product) => (
                    <article key={product.id} className="product-card">
                      <div className="product-card-top">
                        <div>
                          <span className="product-chip">In stock · {product.stock}</span>
                          <strong>{product.name}</strong>
                        </div>
                        <span className="price-badge">${Number(product.price).toFixed(2)}</span>
                      </div>

                      <p>{product.description}</p>

                      <div className="product-card-meta">
                        <span>#{product.id}</span>
                        <span>Stock {product.stock}</span>
                      </div>

                      <div className="action-row compact">
                        <button className="ghost-button" type="button" onClick={() => useProductInForm(product)}>
                          Edit
                        </button>
                        <button className="ghost-button" type="button" onClick={() => useProductForOrder(product)}>
                          Order
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </>
          )}

          {activePage === 'orders' && (
            <>
              <PageCard
                title="Order center"
                description="Place orders with the existing POST /orders endpoint and use the failure path for the cancel test."
                actions={
                  <button className="secondary-button" type="button" onClick={() => void refreshOrders()}>
                    Refresh orders
                  </button>
                }
              >
                <div className="mini-stats">
                  <div className="mini-stat">
                    <span>Checkout</span>
                    <strong>Fast order capture</strong>
                  </div>
                  <div className="mini-stat">
                    <span>Failure path</span>
                    <strong>Cancel uses the existing invalid-order flow</strong>
                  </div>
                </div>

                <div className="callout">
                  The backend does not expose a cancel-order endpoint. The cancel button below intentionally uses the
                  existing invalid-order path so LogSherlock still receives a real backend event.
                </div>

                <form className="form-grid">
                  <Field label="Product">
                    <select
                      value={orderForm.productId}
                      onChange={(event) => setOrderForm({ ...orderForm, productId: event.target.value })}
                    >
                      <option value="">Choose a product</option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          #{product.id} {product.name}
                        </option>
                      ))}
                    </select>
                  </Field>

                  <Field label="Quantity">
                    <input
                      type="number"
                      min="1"
                      value={orderForm.quantity}
                      onChange={(event) => setOrderForm({ ...orderForm, quantity: event.target.value })}
                      placeholder="1"
                    />
                  </Field>

                  <div className="action-row full-span">
                    <button className="primary-button" type="button" onClick={() => void handlePlaceOrder()}>
                      Place order
                    </button>
                    <button className="danger-button" type="button" onClick={() => void handleCancelOrder()}>
                      Cancel order
                    </button>
                  </div>
                </form>
              </PageCard>

              <div className="subsection">
                <div className="subsection-heading">
                  <h3>Latest orders</h3>
                  <span>{loading.orders ? 'Loading...' : `${orders.length} orders`}</span>
                </div>

                <div className="product-grid">
                  {orders.map((order) => (
                    <article key={order.id} className="product-card">
                      <div className="product-card-top">
                        <div>
                          <span className="product-chip">{order.status}</span>
                          <strong>Order #{order.id}</strong>
                        </div>
                        <span className="price-badge">${Number(order.total_amount).toFixed(2)}</span>
                      </div>

                      <p>Product {order.product_id} by {order.username}</p>

                      <div className="product-card-meta">
                        <span>Qty {order.quantity}</span>
                        <span>{order.username}</span>
                      </div>

                      <div className="action-row compact">
                        <button
                          className="ghost-button"
                          type="button"
                          onClick={() => setOrderForm({ ...orderForm, productId: String(order.product_id) })}
                        >
                          Reuse product
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </>
          )}

          {activePage === 'security' && (
            <PageCard
              title="Security checks"
              description="Trigger unauthorized access with the protected profile route and missing credentials."
              actions={
                <button className="secondary-button" type="button" onClick={() => void triggerUnauthorizedAccess()}>
                  Trigger unauthorized access
                </button>
              }
            >
              <div className="callout warning">
                The protected /profile endpoint logs UNAUTHORIZED_ACCESS when the bearer token is missing or invalid.
              </div>

              <div className="feature-grid">
                <article className="feature-card">
                  <p className="eyebrow">Protected route</p>
                  <h3>Missing token</h3>
                  <p>Requests to /profile are rejected without a bearer token, producing an unauthorized event.</p>
                </article>
                <article className="feature-card">
                  <p className="eyebrow">Validation</p>
                  <h3>Invalid token</h3>
                  <p>Try an invalid value to see the same error path handled in the UI.</p>
                </article>
              </div>

              <div className="button-cluster">
                <button className="primary-button" type="button" onClick={() => void triggerUnauthorizedAccess()}>
                  Trigger unauthorized access
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => void apiRequest('/profile', { token: 'invalid-token' }).catch((error) => {
                    addActivity('UNAUTHORIZED_ACCESS', error.message, 'warning');
                    addNotification('warning', 'Invalid token rejected', error.message);
                  })}
                >
                  Try invalid token
                </button>
              </div>
            </PageCard>
          )}

          {activePage === 'system' && (
            <PageCard
              title="System diagnostics"
              description="Check health and exercise the existing backend error flow. APPLICATION_STARTED and APPLICATION_STOPPED are emitted by the Flask process itself."
              actions={
                <button className="secondary-button" type="button" onClick={() => void checkSystemHealth()}>
                  Start application
                </button>
              }
            >
              <div className="callout">
                DemoShop emits APPLICATION_STARTED when the backend process launches and APPLICATION_STOPPED when it
                exits. The UI cannot force those lifecycle hooks without changing the backend, so the buttons below
                stick to the existing HTTP routes.
              </div>

              <div className="feature-grid">
                <article className="feature-card">
                  <p className="eyebrow">Status</p>
                  <h3>Health route</h3>
                  <p>The /health route confirms the backend is reachable without changing the Flask service.</p>
                </article>
                <article className="feature-card">
                  <p className="eyebrow">Failure flow</p>
                  <h3>Test error route</h3>
                  <p>The /test-error route intentionally triggers the backend error flow for observation.</p>
                </article>
              </div>

              <div className="button-cluster">
                <button className="primary-button" type="button" onClick={() => void checkSystemHealth()}>
                  Start application
                </button>
                <button className="danger-button" type="button" onClick={() => void triggerSystemError()}>
                  Stop application
                </button>
              </div>

              <p className="helper-text">
                The stop action uses the existing /test-error route as a visible system-side failure trigger. The
                lifecycle stop event itself still comes from shutting down the backend process.
              </p>
            </PageCard>
          )}
        </section>

        <aside className="secondary-column">
          <PageCard title="Live activity" description="Latest generated events and test actions from this session.">
            <div className="activity-list">
              {activity.length === 0 ? (
                <div className="empty-state">
                  No activity yet. Use the pages on the left to trigger DemoShop events.
                </div>
              ) : (
                activity.map((entry) => (
                  <article key={entry.id} className={`activity-item ${entry.state}`}>
                    <div className="activity-topline">
                      <strong>{entry.eventName}</strong>
                      <span>{entry.timestamp}</span>
                    </div>
                    <p>{entry.detail}</p>
                  </article>
                ))
              )}
            </div>

            <div className="status-grid">
              <StatusTile label="Token" value={token ? 'Stored' : 'Missing'} tone={token ? 'success' : 'warning'} />
              <StatusTile label="Products" value={String(products.length)} tone="info" />
              <StatusTile label="Orders" value={String(orders.length)} tone="info" />
            </div>
          </PageCard>

          <PageCard title="How it works" description="How this UI talks to the existing backend.">
            <ul className="note-list">
              <li>Uses the current Flask routes only.</li>
              <li>Stores the login token locally for protected calls.</li>
              <li>Uses the Vite proxy in development to avoid CORS issues.</li>
              <li>Does not modify backend code, database tables, or logging logic.</li>
            </ul>
          </PageCard>
        </aside>
      </main>
    </div>
  );
}

function getPageFromHash() {
  const rawHash = window.location.hash.replace(/^#\/?/, '');
  const pageName = rawHash || 'login';

  return pageDefinitions.some((page) => page.id === pageName) ? pageName : 'login';
}

function readJsonStorage(key) {
  const storedValue = localStorage.getItem(key);

  if (!storedValue) {
    return null;
  }

  try {
    return JSON.parse(storedValue);
  } catch {
    return null;
  }
}

function PageCard({ title, description, actions, children }) {
  return (
    <article className="page-card">
      <div className="page-card-header">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      {children}
    </article>
  );
}

function Field({ label, children, className = '' }) {
  return (
    <label className={`field ${className}`.trim()}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function StatusTile({ label, value, tone }) {
  return (
    <div className={`status-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;