const path = require('path');
const webpack = require('webpack');
const VueLoaderPlugin = require('vue-loader/lib/plugin');
const TerserPlugin = require('terser-webpack-plugin');
const FileManagerPlugin = require('filemanager-webpack-plugin');

// const isDevServer = process.argv.find(v => v.includes('webpack-dev-server'));

module.exports = (env, options) => {

    exports = {
        entry: './src/main.js',
        output: {
            path: path.resolve(__dirname, '../amd/build'),
            publicPath: '/dist/',
            filename: 'app-lazy.min.js',
            chunkFilename: "[id].app-lazy.min.js?v=[hash]",
            libraryTarget: 'amd',
        },
        module: {
            rules: [
                {
                    test: /\.css$/,
                    use: [
                        'vue-style-loader',
                        'css-loader'
                    ],
                },
                {
                    test: /\.vue$/,
                    loader: 'vue-loader',
                    options: {
                        loaders: {}
                        // Other vue-loader options go here
                    }
                },
                {
                    test: /\.js$/,
                    loader: 'babel-loader',
                    exclude: /node_modules/
                },
                /*{
                    test: /\.tsx?$/,
                    loader: "ts-loader",
                    exclude: /node_modules/,
                    options: {
                        // Tell to ts-loader: if you check .vue file extension, handle it like a ts file
                        appendTsSuffixTo: [/\.vue$/]
                    }
                }*/
            ]
        },
        resolve: {
            alias: {
                'vue$': 'vue/dist/vue.esm.js',
                '@': path.resolve(__dirname, "./src/"),
            },
            extensions: ['*', '.tsx', '.ts', '.js', '.vue', '.json']
        },
        devServer: {
            historyApiFallback: true,
            noInfo: true,
            overlay: true,
            headers: {
                'Access-Control-Allow-Origin': '\*'
            },
            disableHostCheck: true,
            https: true,
            public: 'https://127.0.0.1:8080',
            hot: true,
        },
        performance: {
            hints: false
        },
        devtool: 'source-map', // '#eval-source-map',
        plugins: [
            new VueLoaderPlugin(),
            new FileManagerPlugin({
                events: {
                    onStart: {
                        delete: [
                            {
                                source: path.resolve(__dirname, '../amd/src/app-lazy.js'),
                                options: { force: true },
                            },
                            {
                                source: path.resolve(__dirname, '../amd/build/app-lazy.min.js'),
                                options: { force: true },
                            },
                        ],
                    },
                    onEnd: {
                        copy: [
                            { source: path.resolve(__dirname, '../amd/build'), destination: path.resolve(__dirname, '../amd/src') },
                        ],
                        move: [
                            { source: path.resolve(__dirname, '../amd/src/app-lazy.min.js'), destination: path.resolve(__dirname, '../amd/src/app-lazy.js') },
                        ],
                        delete: [
                            {
                                source: path.resolve(__dirname, '../amd/src/app-lazy.min.js'),
                                options: { force: true },
                            },
                        ],
                    },
                }
            }),
        ],
        watchOptions: {
            ignored: /node_modules/
        },
        externals: {
            'core/ajax': {
                amd: 'core/ajax'
            },
            'core/str': {
                amd: 'core/str'
            },
            'core/modal_factory': {
                amd: 'core/modal_factory'
            },
            'core/modal_events': {
                amd: 'core/modal_events'
            },
            'core/fragment': {
                amd: 'core/fragment'
            },
            'core/yui': {
                amd: 'core/yui'
            },
            'core/localstorage': {
                amd: 'core/localstorage'
            },
            'core/notification': {
                amd: 'core/notification'
            },
            'jquery': {
                amd: 'jquery'
            },
            'jqueryui': {
                amd: 'jqueryui'
            }
        }
    };

    if (options.mode === 'production') {
        exports.devtool = false;
        // http://vue-loader.vuejs.org/en/workflow/production.html
        exports.plugins = (exports.plugins || []).concat([
            new webpack.DefinePlugin({
                'process.env': {
                    NODE_ENV: '"production"'
                }
            }),
            new webpack.LoaderOptionsPlugin({
                minimize: true
            })
        ]);
        exports.optimization = {
            minimizer: [
                new TerserPlugin({
                    cache: true,
                    parallel: true,
                    sourceMap: true,
                    terserOptions: {
                        // https://github.com/webpack-contrib/terser-webpack-plugin#terseroptions
                    }
                }),
            ]
        };
    }

    return exports;
};

