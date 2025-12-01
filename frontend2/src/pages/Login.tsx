import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import { login as loginRequest } from "../services/auth.ts";
import { useAuth } from "../hooks/useAuth.ts";
import { useToast } from "../components/shared/ToastContext.ts";
import { Input } from "../components/shared/Input.tsx";
import { Button } from "../components/shared/Button.tsx";
import { FormField } from "../components/shared/FormField.tsx";
import { Spinner } from "../components/shared/Spinner.tsx";
import { Eye, EyeOff } from "lucide-react";

export const LoginPage = () => {
  const [email, setEmail] = useState("suryaprakashb265@gmail.com");
  const [password, setPassword] = useState("11111111");
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { push } = useToast();

  const mutation = useMutation({
    mutationFn: () => loginRequest({ email, password }),
    onSuccess: (data) => {
      login(data, data.token);
  push({ title: "Welcome back", description: "Let's keep the momentum going!", tone: "success" });
      navigate("/dashboard");
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Unable to sign you in right now.";
      push({ title: "Login failed", description: message, tone: "error" });
    },
  });

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <FormField label="Email">
        <Input
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </FormField>
      <FormField label="Password">
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            className="pr-10"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 transition-colors"
            title={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        </div>
      </FormField>
      <div className="flex items-center justify-between text-xs">
        <div></div>
        <Link to="/forgot-password" className="text-blue-400 hover:text-blue-300">
          Forgot password?
        </Link>
      </div>
      <Button type="submit" disabled={mutation.isPending} className="w-full">
        {mutation.isPending ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner /> Signing in
          </span>
        ) : (
          "Sign in"
        )}
      </Button>
      <p className="text-center text-xs text-slate-500">
        Need an account? <Link to="/signup" className="text-blue-400">Create one</Link>
      </p>
    </form>
  );
};
