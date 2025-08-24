import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/useAuth";
import Dashboard from "@/pages/Dashboard";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Orders from "@/pages/Orders";
import Admin from "@/pages/Admin";
import Register from "@/pages/Register";
import Profile from "@/pages/Profile";
import NotFound from "@/pages/not-found";

function Router() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Switch>
      <Route path="/register" component={Register} />
      <Route path="/login" component={Login} />
      {isLoading || !isAuthenticated ? (
        <>
          <Route path="/" component={Landing} />
          <Route component={Landing} />
        </>
      ) : (
        <>
          <Route path="/" component={() => <Dashboard />} />
          <Route path="/dashboard" component={() => <Dashboard />} />
          <Route path="/tra-cuu-ftth" component={() => <Dashboard initialService="tra_cuu_ftth" />} />
          <Route path="/gach-dien-evn" component={() => <Dashboard initialService="gach_dien_evn" />} />
          <Route path="/nap-tien-da-mang" component={() => <Dashboard initialService="nap_tien_da_mang" />} />
          <Route path="/nap-tien-viettel" component={() => <Dashboard initialService="nap_tien_viettel" />} />
          <Route path="/thanh-toan-tv-internet" component={() => <Dashboard initialService="thanh_toan_tv-internet" />} />
          <Route path="/tra-cuu-no-tra-sau" component={() => <Dashboard initialService="tra_cuu_no_tra_sau" />} />
          <Route path="/profile" component={Profile} />
          <Route path="/orders" component={Orders} />
          <Route path="/admin" component={Admin} />
          <Route component={NotFound} />
        </>
      )}
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
