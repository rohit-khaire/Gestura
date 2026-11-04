import { ScaleLoader } from "react-spinners";

const PageLoader = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-800">
      <ScaleLoader
        color="#fff"
        height={60}
        width={6}
        barCount={6}
        className="text-white size-11 text-primary"
      />
    </div>
  );
};

export default PageLoader;
